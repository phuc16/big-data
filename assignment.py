import streamlit as st
from sentence_transformers import SentenceTransformer, util
import faiss
import numpy as np
import pandas as pd
import os

# === CONFIGURATION ===
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_DATASET_PATH = "semantic_reviews_cleaned.csv"

# === DATASET PREPROCESSING ===
@st.cache_data(show_spinner="Processing data...")
def preprocess_dataset(input_path, output_path="cleaned_reviews_for_semantic_search.csv"):
    df = pd.read_csv(input_path)
    # Remove almost empty columns if they exist
    columns_to_drop = [col for col in ['reviews.didPurchase', 'reviews.id', 'reviews.userCity', 'reviews.userProvince'] if col in df.columns]
    df_cleaned = df.drop(columns=columns_to_drop, errors='ignore')
    # Convert date columns to datetime
    date_columns = [col for col in ['reviews.date', 'reviews.dateAdded', 'reviews.dateSeen'] if col in df_cleaned.columns]
    for col in date_columns:
        df_cleaned[col] = pd.to_datetime(df_cleaned[col], errors='coerce')
    # Keep necessary columns for semantic search/chatbot
    columns_to_keep = [
        'reviews.text', 'reviews.title', 'reviews.rating',
        'reviews.username', 'reviews.date', 'brand',
        'categories', 'manufacturer'
    ]
    columns_to_keep = [col for col in columns_to_keep if col in df_cleaned.columns]
    df_final = df_cleaned[columns_to_keep]
    # Remove rows missing core information
    subset_cols = [col for col in ['reviews.text', 'reviews.title', 'reviews.rating', 'reviews.username', 'reviews.date'] if col in df_final.columns]
    df_final.dropna(subset=subset_cols, inplace=True)
    # Combine reviews.title + reviews.text as semantic search content
    df_final['content'] = df_final['reviews.title'].astype(str) + ": " + df_final['reviews.text'].astype(str)
    # Save file
    df_final.to_csv(output_path, index=False)
    return output_path

# === LOAD MODEL ===
@st.cache_resource(show_spinner="Loading embedding model...")
def load_model():
    return SentenceTransformer(EMBEDDING_MODEL)

# === CREATE FAISS INDEX ===
@st.cache_resource(show_spinner="Creating FAISS index...")
def create_faiss_index(documents, _model):
    # Normalize text
    docs = [str(doc).strip().lower() for doc in documents]
    doc_embeddings = _model.encode(docs, batch_size=64, show_progress_bar=True)
    dimension = doc_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(doc_embeddings))
    return index, doc_embeddings

# === SEMANTIC SEARCH ===
def search_semantic(query, documents, doc_embeddings, model, index, top_k=5):
    query_norm = query.strip().lower()
    query_embedding = model.encode([query_norm])
    distances, indices = index.search(np.array(query_embedding), k=min(top_k, len(documents)))
    candidate_docs = [documents[idx] for idx in indices[0]]
    candidate_embeddings = [doc_embeddings[idx] for idx in indices[0]]
    # Re-ranking
    cosine_scores = util.cos_sim(query_embedding, candidate_embeddings)[0]
    ranked_results = sorted(zip(candidate_docs, cosine_scores), key=lambda x: x[1], reverse=True)
    return ranked_results

# === STREAMLIT UI ===
st.set_page_config(page_title="Semantic Search", page_icon="🔍", layout="wide")
st.title("🔍 Semantic Search + Re-ranking")

model = load_model()

st.markdown("""
**Instructions:**  
- Upload a `.csv` file (with a `content` column) or a `.txt` file (each line is a document).  
- Or choose to use the default dataset.
""")

uploaded_file = st.file_uploader("📄 Upload a .txt or .csv file containing data", type=['txt', 'csv'])
use_default = st.checkbox("Or use the default dataset", value=True)

# Use session state to avoid unnecessary reloads
if "documents" not in st.session_state:
    st.session_state["documents"] = []
if "index" not in st.session_state:
    st.session_state["index"] = None
if "doc_embeddings" not in st.session_state:
    st.session_state["doc_embeddings"] = None

# Load data
if uploaded_file:
    with st.spinner("Reading file..."):
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            if 'content' not in df.columns:
                st.error("CSV file must have a 'content' column.")
                st.stop()
            documents = df['content'].dropna().tolist()
        else:
            content = uploaded_file.read().decode('utf-8')
            documents = [line.strip() for line in content.split('\n') if line.strip()]
        st.session_state["documents"] = documents
        st.success(f"Loaded {len(documents)} documents from file!")
elif use_default:
    with st.spinner("Processing default dataset..."):
        preprocess_dataset(DEFAULT_DATASET_PATH)
        df = pd.read_csv("cleaned_reviews_for_semantic_search.csv")
        documents = df['content'].dropna().tolist()
        st.session_state["documents"] = documents
        st.success(f"Loaded {len(documents)} documents from the default dataset!")
else:
    st.warning("No data available for searching.")

# Create FAISS index if needed
if st.session_state["documents"]:
    if st.session_state["index"] is None or st.session_state["doc_embeddings"] is None:
        with st.spinner("Creating FAISS index..."):
            index, doc_embeddings = create_faiss_index(st.session_state["documents"], model)
            st.session_state["index"] = index
            st.session_state["doc_embeddings"] = doc_embeddings

# Search
st.subheader("🔍 Enter your search query:")
query = st.text_input("Example: 'What should puppies eat?'")
top_k = st.slider("Number of results: ", 1, 10, 5)

if query and st.session_state["index"] is not None:
    with st.spinner("Searching..."):
        ranked_results = search_semantic(query, st.session_state["documents"], st.session_state["doc_embeddings"], model, st.session_state["index"], top_k)
    st.subheader("📚 Semantic Search + Re-ranking Results:")
    for doc, score in ranked_results:
        st.markdown(f"""
        <div style='padding:10px;margin-bottom:10px;border:1px solid #ddd;border-radius:10px;'>
            <b>Document:</b> {doc}<br>
            <b>Relevance:</b> {score.item()*100:.2f}%
        </div>
        """, unsafe_allow_html=True)
elif query:
    st.warning("No data or index available for searching. Please upload data first.")