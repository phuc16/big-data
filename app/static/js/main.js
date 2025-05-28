document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const searchSuggestions = document.getElementById('search-suggestions');
    const searchResults = document.getElementById('search-results');
    const loadingIndicator = document.getElementById('loading-indicator');
    const noResults = document.getElementById('no-results');
    const loadMoreButton = document.getElementById('load-more');
    const applyFiltersButton = document.getElementById('apply-filters');
    const resetFiltersButton = document.getElementById('reset-filters');
    
    let currentPage = 1;
    let currentQuery = '';
    let currentSearchType = 'hybrid';
    let currentFilters = {};
    
    // Search function
    const performSearch = async (query, page = 1, filters = {}) => {
        if (!query) return;
        
        currentQuery = query;
        currentPage = page;
        currentFilters = filters;
        
        // Show loading, hide other elements
        loadingIndicator.classList.remove('d-none');
        searchResults.classList.add('d-none');
        noResults.classList.add('d-none');
        loadMoreButton.classList.add('d-none');
        
        // Get selected search type
        const searchTypeRadio = document.querySelector('input[name="search-type"]:checked');
        currentSearchType = searchTypeRadio ? searchTypeRadio.value : 'hybrid';
        
        // Build URL with query parameters
        let url = `/api/search?q=${encodeURIComponent(query)}&search_type=${currentSearchType}&size=12`;
        
        // Add filters to URL if they exist
        if (filters.categories && filters.categories.length) {
            filters.categories.forEach(cat => {
                url += `&category=${encodeURIComponent(cat)}`;
            });
        }
        
        if (filters.brands && filters.brands.length) {
            filters.brands.forEach(brand => {
                url += `&brand=${encodeURIComponent(brand)}`;
            });
        }
        
        if (filters.manufacturers && filters.manufacturers.length) {
            filters.manufacturers.forEach(manufacturer => {
                url += `&manufacturer=${encodeURIComponent(manufacturer)}`;
            });
        }
        
        if (filters.minRating !== undefined) {
            url += `&min_rating=${filters.minRating}`;
        }
        
        if (filters.maxRating !== undefined) {
            url += `&max_rating=${filters.maxRating}`;
        }
        
        // Execute search
        try {
            const response = await fetch(url);
            const data = await response.json();
            
            // Hide loading indicator
            loadingIndicator.classList.add('d-none');
            searchResults.classList.remove('d-none');
            
            // Display results or no results message
            if (data.results && data.results.length > 0) {
                displayResults(data.results);
                
                // Show "Load More" button if we have enough results
                if (data.results.length === 12) {
                    loadMoreButton.classList.remove('d-none');
                }
            } else {
                noResults.classList.remove('d-none');
            }
            
            // Update facets if available
            if (data.facets) {
                updateFacets(data.facets);
            }
            
        } catch (error) {
            console.error('Search error:', error);
            loadingIndicator.classList.add('d-none');
            noResults.classList.remove('d-none');
        }
    };
    
    // Display search results
    const displayResults = (results) => {
        // Clear previous results if this is the first page
        if (currentPage === 1) {
            searchResults.innerHTML = '';
        }
        
        results.forEach(result => {
            // Create product card
            const productCard = document.createElement('div');
            productCard.className = 'col-md-6 col-lg-4';
            
            // Get product data
            let product;
            if (result._source) {
                // Handle direct Elasticsearch response format
                product = result._source;
                product.id = result._id;
            } else {
                // Handle processed response format
                product = result;
            }
            
            // Get first review for preview
            const firstReview = product.reviews && product.reviews.length > 0 ? product.reviews[0] : null;
            
            // Format categories
            const categories = Array.isArray(product.categories) 
                ? product.categories.slice(0, 3).join(', ')
                : (product.categories || '').split(',').slice(0, 3).join(', ');
                
            // Calculate average rating
            let avgRating = 0;
            let ratingCount = 0;
            
            if (product.reviews && product.reviews.length) {
                const sum = product.reviews.reduce((acc, review) => {
                    if (review.rating) {
                        return acc + review.rating;
                    }
                    return acc;
                }, 0);
                
                ratingCount = product.reviews.length;
                avgRating = ratingCount > 0 ? (sum / ratingCount).toFixed(1) : 0;
            }
            
            // Create HTML for product card
            productCard.innerHTML = `
                <div class="card shadow-sm product-card mb-4">
                    <div class="card-body">
                        <h5 class="card-title">${highlightQuery(product.name, currentQuery)}</h5>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="product-brand">Brand: ${product.brand || 'Unknown'}</span>
                            <span class="product-rating">★ ${avgRating} (${ratingCount})</span>
                        </div>
                        <div class="product-categories mb-2">
                            ${categories.split(',').map(cat => 
                                `<span class="badge rounded-pill category-badge">${cat.trim()}</span>`
                            ).join('')}
                        </div>
                        ${firstReview ? `
                            <div class="review-preview">
                                <h6 class="review-title">${firstReview.title || 'Review'}</h6>
                                <p class="review-text text-muted mb-0">${highlightQuery(truncateText(firstReview.text, 100), currentQuery)}</p>
                            </div>
                        ` : ''}
                    </div>
                    <div class="card-footer bg-transparent">
                        <button class="btn btn-sm btn-outline-secondary w-100 show-details" 
                                data-product-id="${product.id}">
                            View Details
                        </button>
                    </div>
                </div>
            `;
            
            searchResults.appendChild(productCard);
        });
        
        // Add event listeners to "View Details" buttons
        document.querySelectorAll('.show-details').forEach(button => {
            button.addEventListener('click', () => {
                // Implementation for showing product details would go here
                // This could open a modal with detailed product information
                alert(`Product details for ID: ${button.dataset.productId}`);
            });
        });
    };
    
    // Update facets in the UI
    const updateFacets = (facets) => {
        // Implementation would update the filter checkboxes with counts
        console.log('Facets received:', facets);
    };
    
    // Helper function to highlight the search query in text
    const highlightQuery = (text, query) => {
        if (!text || !query) return text || '';
        
        const words = query.split(' ').filter(word => word.length > 2).map(escapeRegExp);
        if (words.length === 0) return text;
        
        const regex = new RegExp(`(${words.join('|')})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    };
    
    // Escape special regex characters
    const escapeRegExp = (string) => {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    };
    
    // Truncate text with ellipsis
    const truncateText = (text, maxLength) => {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    };
    
    // Get search suggestions
    const getSuggestions = async (prefix) => {
        if (prefix.length < 2) {
            searchSuggestions.style.display = 'none';
            return;
        }
        
        try {
            const response = await fetch(`/api/suggestions?prefix=${encodeURIComponent(prefix)}`);
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                displaySuggestions(data.suggestions);
            } else {
                searchSuggestions.style.display = 'none';
            }
        } catch (error) {
            console.error('Error getting suggestions:', error);
            searchSuggestions.style.display = 'none';
        }
    };
    
    // Display search suggestions
    const displaySuggestions = (suggestions) => {
        searchSuggestions.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const div = document.createElement('div');
            div.className = 'search-suggestion';
            div.textContent = suggestion;
            
            div.addEventListener('click', () => {
                searchInput.value = suggestion;
                searchSuggestions.style.display = 'none';
                performSearch(suggestion);
            });
            
            searchSuggestions.appendChild(div);
        });
        
        searchSuggestions.style.display = 'block';
    };
    
    // Gather selected filters
    const gatherFilters = () => {
        const filters = {
            categories: [],
            brands: [],
            manufacturers: [],
            minRating: parseFloat(document.getElementById('min-rating').value),
            maxRating: parseFloat(document.getElementById('max-rating').value)
        };
        
        // Get selected categories
        document.querySelectorAll('input[name="category"]:checked').forEach(checkbox => {
            filters.categories.push(checkbox.value);
        });
        
        // Get selected brands
        document.querySelectorAll('input[name="brand"]:checked').forEach(checkbox => {
            filters.brands.push(checkbox.value);
        });
        
        // Get selected manufacturers
        document.querySelectorAll('input[name="manufacturer"]:checked').forEach(checkbox => {
            filters.manufacturers.push(checkbox.value);
        });
        
        return filters;
    };
    
    // Reset all filters
    const resetFilters = () => {
        document.querySelectorAll('.filter-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        document.getElementById('min-rating').value = 0;
        document.getElementById('min-rating-value').textContent = '0';
        
        document.getElementById('max-rating').value = 5;
        document.getElementById('max-rating-value').textContent = '5';
        
        // Update filter object
        currentFilters = {
            minRating: 0,
            maxRating: 5
        };
        
        // Re-run search if we have a query
        if (currentQuery) {
            performSearch(currentQuery, 1, currentFilters);
        }
    };
    
    // Event Listeners
    
    // Search on button click
    searchButton.addEventListener('click', () => {
        const query = searchInput.value.trim();
        if (query) {
            searchSuggestions.style.display = 'none';
            performSearch(query, 1, gatherFilters());
        }
    });
    
    // Search on Enter key
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                searchSuggestions.style.display = 'none';
                performSearch(query, 1, gatherFilters());
            }
        }
    });
    
    // Get suggestions on input
    let debounceTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            getSuggestions(searchInput.value.trim());
        }, 300);
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
            searchSuggestions.style.display = 'none';
        }
    });
    
    // Load more results
    loadMoreButton.addEventListener('click', () => {
        currentPage++;
        performSearch(currentQuery, currentPage, currentFilters);
    });
    
    // Apply filters
    applyFiltersButton.addEventListener('click', () => {
        const filters = gatherFilters();
        if (currentQuery) {
            performSearch(currentQuery, 1, filters);
        }
    });
    
    // Reset filters
    resetFiltersButton.addEventListener('click', resetFilters);
    
    // Change search type
    document.querySelectorAll('input[name="search-type"]').forEach(radio => {
        radio.addEventListener('change', () => {
            if (currentQuery) {
                performSearch(currentQuery, 1, currentFilters);
            }
        });
    });
});