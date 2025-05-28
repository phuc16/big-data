from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError
import pandas as pd
from app.elasticsearch.client import es_client
from app.config import INDEX_NAME
from app.services.embedding import get_text_embedding

def create_index():
    """Create the index with appropriate mappings for product data"""
    index_settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "custom_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "english_stop", "english_stemmer"]
                    }
                },
                "filter": {
                    "english_stop": {
                        "type": "stop",
                        "stopwords": "_english_"
                    },
                    "english_stemmer": {
                        "type": "stemmer",
                        "language": "english"
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "analyzer": "custom_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        },
                        "completion": {
                            "type": "completion"
                        }
                    }
                },
                "brand": {"type": "keyword"},
                "categories": {"type": "keyword"},
                "manufacturer": {"type": "keyword"},
                "reviews": {
                    "properties": {
                        "date": {"type": "date"},
                        "rating": {"type": "float"},
                        "text": {
                            "type": "text",
                            "analyzer": "custom_analyzer"
                        },
                        "title": {
                            "type": "text",
                            "analyzer": "custom_analyzer"
                        },
                        "username": {"type": "keyword"}
                    }
                },
                "text_vector": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity": "cosine"
                },
                "suggest": {"type": "completion"}
            }
        }
    }
    
    # Create the index
    if not es_client.indices.exists(index=INDEX_NAME):
        es_client.indices.create(index=INDEX_NAME, body=index_settings)
        print(f"Created index '{INDEX_NAME}'")
    else:
        print(f"Index '{INDEX_NAME}' already exists")

def prepare_documents_from_csv(csv_path):
    """
    Process the CSV data and prepare documents for Elasticsearch
    """
    df = pd.read_csv(csv_path)
    
    # Group by product ID to combine reviews
    grouped = df.groupby(['id', 'name', 'brand', 'categories', 'manufacturer'])
    
    documents = []
    
    for (id, name, brand, categories, manufacturer), group in grouped:
        reviews = []
        
        for _, row in group.iterrows():
            if pd.notna(row['reviews.text']):  # Only include reviews with text
                reviews.append({
                    'date': row.get('reviews.date', ''),
                    'rating': float(row.get('reviews.rating', 0)),
                    'text': row.get('reviews.text', ''),
                    'title': row.get('reviews.title', ''),
                    'username': row.get('reviews.username', '')
                })
        
        # Skip products with no reviews
        if not reviews:
            continue
            
        # Create concatenated text for embedding
        text_for_embedding = f"{name} {brand} {categories} " + " ".join([r['text'] for r in reviews])
        
        # Get embedding for the document
        text_embedding = get_text_embedding(text_for_embedding)
        
        document = {
            'id': id,
            'name': name,
            'brand': brand,
            'categories': categories.split(',') if pd.notna(categories) else [],
            'manufacturer': manufacturer if pd.notna(manufacturer) else '',
            'reviews': reviews,
            'text_vector': text_embedding
        }
        
        documents.append({
            "_index": INDEX_NAME,
            "_id": id,
            "_source": document
        })
    
    return documents

def bulk_index_documents(csv_path):
    """Index the documents in bulk"""
    documents = prepare_documents_from_csv(csv_path)
    success, failed = 0, []
    print(f"Prepared {len(documents)} documents for indexing")
    try:
        success, _ = bulk(es_client, documents, refresh=True)
        print(f"Successfully indexed {success} documents. Failed: {failed}")
    except BulkIndexError as e:
        failed = e.errors
        print(f"{len(failed)} document(s) failed to index.")

    return success, failed