from app.elasticsearch.search import (
    basic_search,
    fuzzy_search,
    suggestion_search,
    facet_search,
    semantic_search,
    hybrid_search
)
import re

class SearchService:
    """
    Service layer handling search operations
    """
    
    @staticmethod
    def preprocess_query(query):
        """
        Preprocess search query for better results
        """
        if not query:
            return ""
            
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Remove special characters that might interfere with search
        query = re.sub(r'[^\w\s\']', ' ', query)
        
        # Convert to lowercase
        query = query.lower()
        
        return query
    
    @staticmethod
    def search(query, search_type="basic", filters=None, size=10):
        """
        Execute search based on the specified search type
        """
        processed_query = SearchService.preprocess_query(query)
        if not processed_query:
            return []
        
        if search_type == "basic":
            return basic_search(processed_query, size)
        elif search_type == "fuzzy":
            return fuzzy_search(processed_query, size)
        elif search_type == "faceted":
            return facet_search(processed_query, filters, size)
        elif search_type == "semantic":
            return semantic_search(processed_query, filters, size)
        elif search_type == "hybrid":
            return hybrid_search(processed_query, filters, size)
        else:
            return basic_search(processed_query, size)  # Default to basic search
    
    @staticmethod
    def get_suggestions(prefix, size=5):
        """
        Get search suggestions based on prefix
        """
        return suggestion_search(prefix, size)