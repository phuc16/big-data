from elasticsearch_dsl import Search, Q
from app.elasticsearch.client import es_client
from app.config import INDEX_NAME
from app.services.embedding import get_text_embedding

def basic_search(query, size=10):
    """
    Enhanced basic keyword search with better relevance
    """
    s = Search(using=es_client, index=INDEX_NAME)
    
    # Build the should clauses list
    should_clauses = [
        # Exact matches in name and brand (high boost)
        Q("match_phrase", name={"query": query, "boost": 5.0}),
        Q("match_phrase", brand={"query": query, "boost": 4.0}),
        
        # General field matching
        Q("multi_match", 
          query=query, 
          fields=["name^3", "brand^2", "categories", "reviews.text", "reviews.title^2"],
          type="best_fields",
          minimum_should_match="30%")
    ]
    
    # Conditionally add the phrase_prefix query only if query has fewer than 3 words
    if len(query.split()) < 3:
        should_clauses.append(
            Q("multi_match",
              query=query,
              fields=["name", "reviews.title", "reviews.text"],
              type="phrase_prefix")
        )
    
    # Create the bool query with the should clauses
    q = Q("bool", should=should_clauses)
    
    s = s.query(q)
    
    # Add highlighting
    s = s.highlight_options(pre_tags=['<strong>'], post_tags=['</strong>'])
    s = s.highlight('name', 'brand', 'reviews.text', 'reviews.title')
    
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
            if field == "reviews.rating" and isinstance(values, dict) and "range" in values:
                # Handle rating range filter
                range_params = values["range"]
                s = s.filter("range", **{field: range_params})
            elif isinstance(values, list):
                # Create a should query for multiple values of the same field (OR operation)
                if values:  # Only if the list is not empty
                    should_queries = [Q("term", **{field: value}) for value in values]
                    s = s.filter('bool', should=should_queries, minimum_should_match=1)
            else:
                # Single value filter
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
    
    # Limit size
    s = s[0:size]
    
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

def semantic_search(query, filters=None, size=10):
    """
    Semantic search using vector embeddings with pre-filtering
    """
    # Get vector embedding for the query
    query_vector = get_text_embedding(query)
    
    # Create filter queries if filters are provided
    filter_queries = []
    if filters:
        for field, values in filters.items():
            if field == "reviews.rating" and isinstance(values, dict) and "range" in values:
                # Handle rating range filter
                range_params = values["range"]
                filter_queries.append({"range": {field: range_params}})
            elif isinstance(values, list):
                # Handle list of values (OR operation)
                if values:
                    terms_query = {"terms": {field: values}}
                    filter_queries.append(terms_query)
            else:
                # Handle single value
                filter_queries.append({"term": {field: values}})
    
    # Construct the search body with knn as a top-level parameter
    search_body = {
        "size": size,
        "_source": ["id", "name", "brand", "categories", "reviews"],
        "knn": {
            "field": "text_vector",
            "query_vector": query_vector,
            "k": size,
            "num_candidates": 100
        }
    }
    
    # Add filter if needed
    if filter_queries:
        search_body["knn"]["filter"] = {
            "bool": {
                "filter": filter_queries
            }
        }
    
    response = es_client.search(
        index=INDEX_NAME,
        body=search_body
    )
    
    return response["hits"]["hits"]

def hybrid_search(query, filters=None, size=10):
    """
    Hybrid search combining keyword and semantic search with improved relevance
    """
    # Get vector embedding for the query
    query_vector = get_text_embedding(query)
    
    # Create filter queries if filters are provided
    filter_queries = []
    if filters:
        for field, values in filters.items():
            if field == "reviews.rating" and isinstance(values, dict) and "range" in values:
                # Handle rating range filter
                range_params = values["range"]
                filter_queries.append({"range": {field: range_params}})
            elif isinstance(values, list):
                # Handle list of values (OR operation)
                if values:
                    terms_query = {"terms": {field: values}}
                    filter_queries.append(terms_query)
            else:
                # Handle single value
                filter_queries.append({"term": {field: values}})
    print(f"Hybrid search filters: {filter_queries}")
    # Prepare the hybrid query with required keyword match
    hybrid_query = {
        "bool": {
            "must": [
                # Require at least some keyword match (filters out completely irrelevant docs)
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^3", "brand^2", "categories", "reviews.text", "reviews.title^2"],
                        "minimum_should_match": "30%"  # At least 30% of terms must match
                    }
                }
            ],
            "should": [
                # Boost score with more specific keyword match
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^4", "brand^3", "categories^2", "reviews.text", "reviews.title^2"],
                        "type": "phrase",  # Favor exact phrases
                        "boost": 2.0
                    }
                },
                # Vector similarity with controlled influence
                {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'text_vector') * 0.5",  # Reduced from 0.7
                            "params": {"query_vector": query_vector}
                        }
                    }
                }
            ],
            "filter": filter_queries
        }
    }
    print(f"Final query: {hybrid_query}")
    response = es_client.search(
        index=INDEX_NAME,
        body={
            "size": size,
            "query": hybrid_query,
            "_source": ["id", "name", "brand", "categories", "reviews"],
            "highlight": {
                "fields": {
                    "name": {},
                    "reviews.text": {},
                    "reviews.title": {},
                },
                "pre_tags": ["<strong>"],
                "post_tags": ["</strong>"]
            }
        }
    )
    
    return response["hits"]["hits"]