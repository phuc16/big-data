import uvicorn
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
import os
import json

from app.elasticsearch.index import create_index, bulk_index_documents
from app.utils.data_loader import create_metadata_file
from app.services.search import SearchService

from app.config import (
    DATA_CSV_PATH,
    DATA_METADATA_PATH,
)

app = FastAPI(title="Amazon Product Search")

# Mount static files and templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
create_index()
print("Index creation complete.")

# Create metadata file
print(f"Creating metadata file at {DATA_METADATA_PATH}...")
metadata = create_metadata_file(DATA_CSV_PATH, DATA_METADATA_PATH)
print(f"Created metadata with {len(metadata['categories'])} categories, {len(metadata['brands'])} brands, and {len(metadata['manufacturers'])} manufacturers")

# Index documents
print(f"Indexing documents from {DATA_CSV_PATH}...")
success, failed = bulk_index_documents(DATA_CSV_PATH)
print(f"Indexing complete. Successfully indexed: {success}, Failed: {failed}")

# Load metadata for filtering options
with open(os.path.join("data", "metadata.json"), "r") as f:
    metadata = json.load(f)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main search page"""
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "categories": metadata["categories"],
            "brands": metadata["brands"],
            "manufacturers": metadata["manufacturers"]
        }
    )

@app.get("/api/search")
async def search(
    q: str = Query(..., min_length=1),
    search_type: str = Query("hybrid", regex="^(basic|fuzzy|faceted|semantic|hybrid)$"),
    category: Optional[List[str]] = Query(None),
    brand: Optional[List[str]] = Query(None),
    manufacturer: Optional[str] = Query(None),
    min_rating: float = Query(0.0, ge=0.0, le=5.0),
    max_rating: float = Query(5.0, ge=0.0, le=5.0),
    size: int = Query(10, ge=1, le=100)
):
    """
    Search API endpoint
    """
    # Prepare filters
    filters = {}
    if category:
        filters["categories"] = category
    if brand:
        filters["brand"] = brand
    if manufacturer:
        filters["manufacturer"] = manufacturer

    print(f"Search query: {q}, Type: {search_type}, Filters: {filters}, Size: {size}")
        
    # Add rating filter
    if min_rating > 0.0 or max_rating < 5.0:
        filters["reviews.rating"] = {
            "range": {
                "gte": min_rating,
                "lte": max_rating
            }
        }
    
    # Execute search
    if search_type == "faceted":
        results = SearchService.search(q, search_type=search_type, filters=filters, size=size)
        return {
            "results": [hit.to_dict() for hit in results["hits"]],
            "facets": {
                "brands": [{"key": bucket.key, "doc_count": bucket.doc_count} for bucket in results["facets"]["brands"]],
                "categories": [{"key": bucket.key, "doc_count": bucket.doc_count} for bucket in results["facets"]["categories"]],
                "manufacturers": [{"key": bucket.key, "doc_count": bucket.doc_count} for bucket in results["facets"]["manufacturers"]],
                "ratings": [{"key": bucket.key, "doc_count": bucket.doc_count} for bucket in results["facets"]["ratings"]]
            }
        }
    else:
        # For non-faceted search types, we need to apply the filters in the service layer
        results = SearchService.search(q, search_type=search_type, filters=filters, size=size)
        if search_type in ["semantic", "hybrid"]:
            # Format results from direct ES response
            return {
                "results": [{"id": hit["_id"], **hit["_source"]} for hit in results]
            }
        else:
            # Format results from elasticsearch_dsl response
            return {
                "results": [hit.to_dict() for hit in results]
            }

@app.get("/api/suggestions")
async def suggestions(prefix: str = Query(..., min_length=1)):
    """
    Get search suggestions based on prefix
    """
    suggestions = SearchService.get_suggestions(prefix)
    return {"suggestions": suggestions}

@app.post("/api/index")
async def index_data(csv_path: str = Form(...)):
    """
    Create index and load data (admin operation)
    """
    try:
        # Create the index
        create_index()
        
        # Index the documents
        success, failed = bulk_index_documents(csv_path)
        
        return {
            "success": True,
            "indexed_documents": success,
            "failed_documents": failed
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)