# Datasets Loader for Elasticsearch

This project is designed to load [Hugging Face's datasets](https://huggingface.co/docs/datasets/index) into an Elasticsearch cluster, especially for (but not limited to) wikipedia datasets.

For the search projects, enough amount of test data is crucial for the relevance and performance tuning. This repository provides the data ingestion tool based on Hugging Face's Datasets library which has various of the test datasets such as wikipedia corpus for the text data.

## Setup

1. **Create a virtual environment:**

    ```sh
    python -m venv .venv
    ```

2. **Activate the virtual environment:**

    ```sh
    # On Unix or MacOS
    source .venv/bin/activate

    # On Windows
    .venv\Scripts\activate
    ```

3. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

## Configuration

Create a `.env` file in the root directory of the project by copying `env.sample` file and set the following environment variables:

```env
ES_URL=https://your-elasticsearch-url
ES_USERNAME=your-username
ES_PASSWORD=your-password
# ES_API_KEY=your-api-key

# Target index name
#INDEX_NAME=datasets_wikipedia_en

# If INDEX_NAME is not given, target index name will be:
# {INDEX_PREFIX}-{PATH}-{DATASET_NAME}
# where PATH is the DATASET_PATH with / replaced by _
# Default INDEX_PREFIX is "datasets"
#INDEX_PREFIX=datasets

# Dataset information
# You can find the available datasets from:
# https://huggingface.co/datasets/wikimedia/wikipedia/tree/main
DATASET_PATH=wikimedia/wikipedia
DATASET_NAME=20231101.en
# DATASET_NAME=20231101.ja

# Set to true to delete and recreate the index
RENEW_INDEX=false

# Set the number of documents to bulk index per batch
BULK_SIZE=100
# Set the number of documents to ingest
NUM_INGEST=100
# Set the number of threads to use for bulk indexing
BULK_THREADS=8

# Set the random seed for reproducibility
# If not set, it will load the data from the beginning
# RANDOM_SEED=42
```

If you don't specify `RANDOM_SEED`, this tool ingest `NUM_INGEST` numbers of the documents from the begginging of the dataset.
If `RANDOM_SEED` is given, the documents will be picked randomly. But setting a random seed ensures which documents are selected for each execution with the same seed, so that you can reproduce exactly the same results everytime.

## Set index template

Put index template into Elasticsearch if it's required. You can find a sample API call in the `templates` directory.

## Load the datasets into Elasticsearch

To load the datasets into Elasticsearch, use the following command:

```sh
python es_datasets_loader.py
```

> [!IMPORTANT]
> Once you execute the script, it automatically download the dataset into your computer and it may be quite large. For example, the size of `20231101.en` dataset is around 20GB. About datasets, check out next section.

## Data structure

Default target index name is:

```
{INDEX_PREFIX}-{path}-{DATASET_NAME}
```

where `path` is the DATASET_PATH with `/` replaced by `_`, for example: `datasets-wikimedia_wikipedia-20231101.en`.

Here is the example document:


```json
{
  "_index": "datasets-wikimedia_wikipedia-20231101.en",
  "_id": "12",
  "_score": 1,
  "_source": {
    "id": "12",
    "url": "https://en.wikipedia.org/wiki/Anarchism",
    "title": "Anarchism",
    "text": """Anarchism is a political philosophy and movement that is skeptical of all justifications for authority and seeks to abolish the institutions it claims maintain unnecessary coercion and hierarchy, typically including nation-states, and capitalism. Anarchism advocates for the replacement of the state with stateless societies and voluntary free associations. As a historically left-wing movement, this reading of anarchism is placed on the farthest left of the political spectrum, usually described as the libertarian wing of the socialist movement (libertarian socialism).
(...sip...)
    """,
    "dataset": {
      "type": "Hugging Face Datasets",
      "path": "wikimedia/wikipedia",
      "name": "20231101.en",
      "lang": "en"
    }
  }
}
```

## Datasets

Datasets is the Python library which can load the sample datasets from many places. You can find the available datasets from [here](https://huggingface.co/datasets).

By default, datasets library stores the cache data under `~/.cache/huggingface/datasets`.

### Wikipedia

[Wikipedia datasets](https://huggingface.co/datasets/wikimedia/wikipedia) is a real text contents form the [Wikipedia](https://www.wikipedia.org/).
It contains cleaned articles of all languages.

The path to the dataset is `wikimedia/wikipedia`

There are many datasets for each language. Refer to the below URL for the available names: 
https://huggingface.co/datasets/wikimedia/wikipedia/tree/main
