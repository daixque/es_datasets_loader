import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import parallel_bulk
from datasets import load_dataset
import time

load_dotenv()

ES_API_KEY = os.getenv('ES_API_KEY')
ES_URL = os.getenv('ES_URL')
ES_USERNAME = os.getenv('ES_USERNAME')
ES_PASSWORD = os.getenv('ES_PASSWORD')

def build_elasticsearch_client():
    if ES_API_KEY:
        return Elasticsearch(
            ES_URL,
            api_key=ES_API_KEY,
            request_timeout=60,
        )
    else:
        return Elasticsearch(
            ES_URL,
            basic_auth=(ES_USERNAME, ES_PASSWORD),
            request_timeout=60,
        )

try:
    es_client = build_elasticsearch_client()
    es_cluster_info = es_client.info()
    print(f'Connected to Elasticsearch cluster: {es_cluster_info["cluster_name"]} ({es_cluster_info["version"]["number"]})')
except Exception as e:
    print(f'Error connecting to Elasticsearch: {e}')
    exit(1)

INDEX_NAME = os.getenv('INDEX_NAME', None)
INDEX_PREFIX = os.getenv('INDEX_PREFIX', 'datasets')
RENEW_INDEX = os.getenv('RENEW_INDEX', 'false').lower() == 'true'
BULK_SIZE = int(os.getenv('BULK_SIZE', 100))
BULK_THREADS = int(os.getenv('BULK_THREADS', 8))
NUM_INGEST = int(os.getenv('NUM_INGEST', 1000))

DATASET_PATH = os.getenv('DATASET_PATH', 'wikimedia/wikipedia')
DATASET_NAME = os.getenv('DATASET_NAME', '20220301.en')
DATASET_STREAMING = os.getenv('DATASET_STREAMING', 'false').lower() == 'true'

sprit = DATASET_NAME.split('.')
if len(sprit) == 2:
    LANG = sprit[1]
else:
    LANG = 'unknown'

RANDOM_SEED = os.getenv('RANDOM_SEED', None)
if RANDOM_SEED is not None:
    RANDOM_SEED = int(RANDOM_SEED)

def load_corpus(dataset_path, dataset_name):
    wikipedia = load_dataset(dataset_path, dataset_name, streaming=DATASET_STREAMING, trust_remote_code=True)
    if RANDOM_SEED is not None:
        wikipedia = wikipedia.shuffle(seed=RANDOM_SEED)
    return wikipedia['train']

def delete_index_if_exists(index_name):
    if es_client.indices.exists(index=index_name):
        es_client.indices.delete(index=index_name)

def create_index_name():
    if INDEX_NAME != None:
        return INDEX_NAME
    path = DATASET_PATH.replace('/', '_')
    return f'{INDEX_PREFIX}-{path}-{DATASET_NAME}'

# Upload the corpus to the Elasticsearch server
def upload_corpus(corpus):
    index_name = create_index_name()
    if RENEW_INDEX:
        delete_index_if_exists(index_name)
    success_count = 0
    error_count = 0
    error_docs = []

    def gendata():
        for doc in corpus:
            if success_count >= NUM_INGEST:
                break
            doc['dataset'] = {
                'type': 'Hugging Face Datasets',
                'path': DATASET_PATH,
                'name': DATASET_NAME,
                'lang': LANG,
            }
            yield {
                '_index': index_name,
                '_id': doc['id'],
                '_source': doc
            }

    print(f'Uploading {NUM_INGEST} documents to the Elasticsearch server')

    start_time = time.time()
    for success, info in parallel_bulk(
        es_client,
        gendata(),
        thread_count=BULK_THREADS,
        queue_size=BULK_THREADS * 2,
        chunk_size=BULK_SIZE,
        raise_on_error=False
    ):
        if success:
            success_count += 1
            if success_count % BULK_SIZE == 0:
                print(f'{success_count} documents uploaded')
        else:
            error_count += 1
            error_docs.append(info['index']['_id'])
        if success_count >= NUM_INGEST:
            break
    end_time = time.time()
    print(f'Total {success_count} documents uploaded successfully')
    print(f'{error_count} documents failed to upload')
    print(f'Error documents: {error_docs}')
    # print the throughput (documents per second)
    print(f'Elapsed time: {end_time - start_time:.2f} seconds')
    print(f'Throughput: {success_count / (end_time - start_time):.2f} docs/sec')


if __name__ == '__main__':
    print(f'Target dataset: {DATASET_PATH}, {DATASET_NAME}')
    corpus = load_corpus(DATASET_PATH, DATASET_NAME)
    upload_corpus(corpus)
    print(f'All documents are uploaded to the Elasticsearch server')
