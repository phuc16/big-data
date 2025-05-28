from elasticsearch import Elasticsearch
from app.config import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_PORT,
    ELASTICSEARCH_USERNAME,
    ELASTICSEARCH_PASSWORD
)

def get_elasticsearch_client():
    """Create and return Elasticsearch client instance"""
    connection_params = {
        "hosts": [f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}"]
    }
    
    if ELASTICSEARCH_USERNAME and ELASTICSEARCH_PASSWORD:
        connection_params["basic_auth"] = (ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD)
        
    return Elasticsearch(**connection_params)

es_client = get_elasticsearch_client()