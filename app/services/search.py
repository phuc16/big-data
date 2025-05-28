from app.elasticsearch.search import (
    basic_search,
    fuzzy_search,
    suggestion_search,
    facet_search,
    semantic_search,
    hybrid_search
)

class SearchService:
    """
    Service layer handling search operations
    """
    
    @staticmethod
    def search(query, search_type="basic", filters=None, size=10):
        """
        Execute search based on the specified search type
        """
        if not query:
            return []
        
        if search_type == "basic":
            return basic_search(query, size)
        elif search_type == "fuzzy":
            return fuzzy_search(query, size)
        elif search_type == "faceted":
            return facet_search(query, filters, size)
        elif search_type == "semantic":
            return semantic_search(query, size)
        elif search_type == "hybrid":
            return hybrid_search(query, size)
        else:
            return basic_search(query, size)  # Default to basic search
    
    @staticmethod
    def get_suggestions(prefix, size=5):
        """
        Get search suggestions based on prefix
        """
        return suggestion_search(prefix, size)