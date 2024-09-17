import google.generativeai as genai
import os
from numpy import dot
from numpy.linalg import norm
from app.mcc import get_mcc_description  

genai.configure(api_key=os.getenv("API_KEY"))

def generate_embedding_with_gemini(text):
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
            title="Embedding for transaction data"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def generate_combined_embedding(merchant_name, city, mcc, country):
    mcc_description = get_mcc_description(mcc)  
    combined_text = f"{merchant_name} {city} {mcc_description if mcc_description else mcc} {country}"
    return generate_embedding_with_gemini(combined_text)

def generate_brand_embedding(name, category, website, country):
    combined_text = f"{name} {category} {website} {country}"
    return generate_embedding_with_gemini(combined_text)

def cosine_similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))
