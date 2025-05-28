import os

# Elasticsearch configuration
DATA_CSV_PATH = os.environ.get("DATA_CSV", "data/data.csv")
DATA_METADATA_PATH = os.environ.get("DATA_METADATA", "data/metadata.json")
ELASTICSEARCH_HOST = os.environ.get("ELASTICSEARCH_HOST", "localhost")
ELASTICSEARCH_PORT = int(os.environ.get("ELASTICSEARCH_PORT", 9200))
ELASTICSEARCH_USERNAME = os.environ.get("ELASTICSEARCH_USERNAME", "")
ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD", "")

# Index settings
INDEX_NAME = "amazon_products"
EMBEDDING_DIMENSION = 384  # Default for sentence-transformers/all-MiniLM-L6-v2