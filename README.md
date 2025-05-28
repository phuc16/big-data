# Amazon Product Search with Elasticsearch

This application provides a smart search interface for Amazon product reviews, showcasing various advanced search capabilities:

1. **Basic Keyword Search** - Standard text search across product and review data
2. **Fuzzy Search** - Handles typos and spelling errors in search queries
3. **Faceted Search** - Filter results by categories, brands, manufacturers, and ratings
4. **Semantic Search** - Vector-based search using sentence embeddings for meaning-based search
5. **Hybrid Search** - Combines traditional keyword search with semantic search for optimal results

## Setup and Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.8+
- 8GB+ RAM (recommended for Elasticsearch and the embedding model)

### Running with Docker

1. Clone the repository:
```
git clone https://github.com/yourusername/amazon-product-search.git
cd amazon-product-search
```

2. Start the services:
```
docker-compose up -d
```

3. Access the application at http://localhost:8000

### Running Locally

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Start Elasticsearch (using Docker or local installation)

3. Start the application:
```
uvicorn app.main:app --reload
```

## Features

### Smart Search Capabilities

- **Autocomplete** - Get suggestions as you type
- **Spelling correction** - Find products even with misspelled queries
- **Semantic understanding** - Find products by meaning, not just keywords
- **Smart filtering** - Filter products by various attributes

### API Endpoints

- `GET /api/search` - Search for products with various options
  - Parameters:
    - `q`: Search query (required)
    - `search_type`: Type of search (basic, fuzzy, faceted, semantic, hybrid)
    - `category`, `brand`, `manufacturer`: Filter parameters
    - `min_rating`, `max_rating`: Filter by review rating
    - `size`: Number of results to return

- `GET /api/suggestions` - Get search suggestions
  - Parameters:
    - `prefix`: Input text to generate suggestions

## Tech Stack

- **FastAPI** - Web framework
- **Elasticsearch** - Search engine
- **Sentence Transformers** - For semantic embeddings
- **Pandas** - Data processing
- **Bootstrap** - UI framework