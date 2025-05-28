from elasticsearch_dsl import Search, Q
from app.elasticsearch.client import es_client
from app.config import INDEX_NAME
from app.services.embedding import get_text_embedding

def basic_search(query, size=10):
    """
    Basic keyword search using the query string
    """
    s = Search(using=es_client, index=INDEX_NAME)
    q = Q("multi_match", query=query, fields=["name^3", "brand^2", "categories", "reviews.text", "reviews.title^2"])
    s = s.query(q)
    response = s.execute()
    
    return response.hits

def fuzzy_search(query, size=10):
    """
    Fuzzy search to handle typos and spelling errors
    """
    s = Search(using=es_client, index=INDEX_NAME)
    
    # Multi-match with fuzziness
    q = Q("multi_match", 
          query=query, 
          fields=["name^3", "brand^2", "categories", "reviews.text", "reviews.title^2"],
          fuzziness="AUTO")
    
    s = s.query(q)
    response = s.execute()
    
    return response.hits

def suggestion_search(prefix, size=5):
    """
    Provide search suggestions based on product name
    """
    suggest_query = {
        "suggest": {
            "name-suggest": {
                "prefix": prefix,
                "completion": {
                    "field": "name.completion",
                    "size": size
                }
            }
        }
    }
    
    response = es_client.search(index=INDEX_NAME, body=suggest_query)
    suggestions = response["suggest"]["name-suggest"][0]["options"]
    
    return [suggestion["text"] for suggestion in suggestions]

def facet_search(query, filters=None, size=10):
    """
    Faceted search with filtering
    """
    s = Search(using=es_client, index=INDEX_NAME)
    
    # Base query
    base_query = Q("multi_match", query=query, fields=["name^3", "brand^2", "categories", "reviews.text", "reviews.title^2"])
    s = s.query(base_query)
    
    # Apply filters if provided
    if filters:
        for field, values in filters.items():
            if isinstance(values, list):
                for value in values:
                    s = s.filter("term", **{field: value})
            else:
                s = s.filter("term", **{field: values})
    
    # Add aggregations for facets
    s.aggs.bucket("brands", "terms", field="brand", size=20)
    s.aggs.bucket("categories", "terms", field="categories", size=20)
    s.aggs.bucket("manufacturers", "terms", field="manufacturer", size=20)
    s.aggs.bucket("ratings", "range", field="reviews.rating", ranges=[
        {"to": 1.0},
        {"from": 1.0, "to": 2.0},
        {"from": 2.0, "to": 3.0},
        {"from": 3.0, "to": 4.0},
        {"from": 4.0, "to": 5.0},
        {"from": 5.0}
    ])
    
    response = s.execute()
    
    return {
        "hits": response.hits,
        "facets": {
            "brands": response.aggregations.brands.buckets,
            "categories": response.aggregations.categories.buckets,
            "manufacturers": response.aggregations.manufacturers.buckets,
            "ratings": response.aggregations.ratings.buckets
        }
    }

def semantic_search(query, size=10):
    """
    Semantic search using vector embeddings
    """
    # Get vector embedding for the query
    query_vector = get_text_embedding(query)
    
    # Perform vector search
    vector_query = {
        "knn": {
            "field": "text_vector",
            "query_vector": query_vector,
            "k": size,
            "num_candidates": 100
        }
    }
    
    response = es_client.search(
        index=INDEX_NAME,
        body={
            "size": size,
            "query": vector_query,
            "_source": ["id", "name", "brand", "categories", "reviews"]
        }
    )
    
    return response["hits"]["hits"]

def hybrid_search(query, size=10):
    """
    Hybrid search combining keyword and semantic search
    """
    # Get vector embedding for the query
    query_vector = get_text_embedding(query)
    
    # Prepare the hybrid query
    hybrid_query = {
        "bool": {
            "should": [
                # Keyword match (BM25)
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^3", "brand^2", "categories", "reviews.text", "reviews.title^2"],
                        "boost": 0.4
                    }
                },
                # Vector similarity
                {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'text_vector') + 1.0",
                            "params": {"query_vector": query_vector}
                        }
                    }
                }
            ]
        }
    }
    
    response = es_client.search(
        index=INDEX_NAME,
        body={
            "size": size,
            "query": hybrid_query,
            "_source": ["id", "name", "brand", "categories", "reviews"]
        }
    )
    
    return response["hits"]["hits"]