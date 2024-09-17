from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import get_db_conn, release_db_conn
import re
from fuzzywuzzy import fuzz
import unicodedata

location_router = APIRouter()

class BranchRequest(BaseModel):
    merchant_name: str
    city: str
    brand_name: str
    
def extract_store_id(merchant_name, brand):
    if brand == "Zabka":
        match = re.search(r'Z\d{3,4}', merchant_name) 
        return match.group(0) if match else None
    return None

def fuzzy_match_score(a, b):
    return fuzz.ratio(a.lower(), b.lower())

def normalize_string(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')

@location_router.post("/get-branch")
def get_branch(branch_request: BranchRequest):
    merchant_name = branch_request.merchant_name
    city = branch_request.city
    brand_name = branch_request.brand_name

    extracted_store_id = extract_store_id(merchant_name, brand_name)

    if not extracted_store_id:
        raise HTTPException(status_code=400, detail=f"Could not extract store_id from merchant_name: {merchant_name}")

    normalized_city = normalize_string(city)

    conn = get_db_conn()
    if conn:
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT store_id, street, town, store_url 
                FROM locations 
                WHERE store_id = %s
            """, (extracted_store_id,))
            
            exact_match_results = cur.fetchall()

            if exact_match_results:
                result = exact_match_results[0]
                return {
                    "store_id": result[0],
                    "town": result[2],
                    "street": result[1],
                    "store_url": result[3],
                    "brand_name": brand_name,
                    "store_id_score": 100,
                    "city_score": fuzzy_match_score(normalized_city, normalize_string(result[2])),
                    "combined_confidence": 100  
                }

            cur.execute("""
                SELECT store_id, street, town, store_url 
                FROM locations 
                WHERE store_id LIKE %s
            """, (f'{extracted_store_id}%',)) 
            
            partial_results = cur.fetchall()

            if not partial_results:
                raise HTTPException(status_code=404, detail="No matching branches found")

            filtered_results = [result for result in partial_results if fuzzy_match_score(normalized_city, normalize_string(result[2])) >= 80]

            if len(filtered_results) > 1:
                return {"message": "Sorry, more than one possible store"}

            best_match = None
            best_score = 0

            for result in filtered_results:
                db_store_id, street, town, store_url = result

                store_id_score = fuzzy_match_score(extracted_store_id, db_store_id)
                city_score = fuzzy_match_score(normalized_city, normalize_string(town))

                combined_confidence = (store_id_score * 0.7 + city_score * 0.3)

                if combined_confidence > best_score:
                    best_score = combined_confidence
                    best_match = {
                        "store_id": db_store_id,
                        "town": town,
                        "street": street,
                        "store_url": store_url,
                        "brand_name": brand_name,
                        "store_id_score": store_id_score,
                        "city_score": city_score,
                        "combined_confidence": combined_confidence
                    }

            if not best_match or best_score < 70: 
                raise HTTPException(status_code=404, detail="No confident match found for the provided store_id and city")

            return best_match

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching branch: {e}")
        finally:
            release_db_conn(conn)
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to the database")