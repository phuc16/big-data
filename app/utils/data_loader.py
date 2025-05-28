import pandas as pd
import os
import json

def load_csv_data(csv_path):
    """
    Load data from CSV file
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    return df

def get_unique_categories(df):
    """
    Extract all unique categories from the dataset
    """
    categories = set()
    for cat_list in df['categories'].dropna():
        for cat in cat_list.split(','):
            categories.add(cat.strip())
    
    return sorted(list(categories))

def get_unique_brands(df):
    """
    Extract all unique brands from the dataset
    """
    return sorted(df['brand'].dropna().unique().tolist())

def get_unique_manufacturers(df):
    """
    Extract all unique manufacturers from the dataset
    """
    return sorted(df['manufacturer'].dropna().unique().tolist())

def create_metadata_file(csv_path, output_path):
    """
    Create metadata file with categories, brands, and manufacturers
    """
    df = load_csv_data(csv_path)
    
    metadata = {
        "categories": get_unique_categories(df),
        "brands": get_unique_brands(df),
        "manufacturers": get_unique_manufacturers(df)
    }
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata