import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import (
    EMBEDDING_DIMENSION
)

# Load the model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def get_text_embedding(text):
    """
    Get vector embedding for text using sentence transformers
    """
    if not text or len(text.strip()) < 3:
        return np.zeros(EMBEDDING_DIMENSION).tolist()  # Return zero vector if text is empty
    
    text = text.lower().strip()
    
    # Truncate text if too long (prevent memory issues)
    if len(text) > 100000:
        text = text[:100000]
        
    # Generate embedding
    embedding = model.encode(text)
    
    return embedding.tolist()