from fastapi import APIRouter, HTTPException
from models.transactions import Transaction 
from db import get_db_conn, release_db_conn
from embeddings import generate_combined_embedding, cosine_similarity
from mcc import get_mcc_description 
import logging

transaction_router = APIRouter()

logging.basicConfig(level=logging.INFO)

@transaction_router.post("/add-transaction")
def add_transaction(transaction: Transaction):
    conn = get_db_conn()
    if conn:
        try:
            cur = conn.cursor()

            mcc_description = get_mcc_description(transaction.mcc)
            if not mcc_description:
                raise HTTPException(status_code=400, detail=f"MCC {transaction.mcc} not found")

            logging.info(f"Fetched MCC description for {transaction.mcc}: {mcc_description}")

            embedding = generate_combined_embedding(
                transaction.merchant_name, 
                transaction.city, 
                mcc_description, 
                transaction.country
            )

            if not embedding:
                logging.error(f"Failed to generate embedding for transaction: {transaction}")
                raise HTTPException(status_code=500, detail="Failed to generate embedding")

            cur.execute("""
                INSERT INTO transactions (merchant_name, city, mcc, country, embedding)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (transaction.merchant_name, transaction.city, transaction.mcc, transaction.country, embedding))
            
            transaction_id = cur.fetchone()[0]
            logging.info(f"Transaction added with ID {transaction_id}")

            cur.execute("SELECT id, name, category, website, country, embedding FROM brands")
            brands = cur.fetchall()

            best_match = None
            best_score = 0

            for brand in brands:
                brand_id = brand[0]
                brand_name = brand[1]
                brand_category = brand[2]
                brand_website = brand[3]
                brand_country = brand[4]
                brand_embedding = brand[5]

                score = cosine_similarity(embedding, brand_embedding)

                logging.info(f"Comparing with brand {brand_name}: score {score}")

                if score > best_score:
                    best_score = score
                    best_match = {
                        "brand_name": brand_name,
                        "category": brand_category,
                        "website": brand_website,
                        "country": brand_country,
                    }

            if best_match and best_score > 0.91: 
                cur.execute("""
                    UPDATE transactions
                    SET brand_name = %s, confidence_score = %s
                    WHERE id = %s
                """, (best_match["brand_name"], float(best_score), transaction_id))

            else:
                logging.warning(f"No confident match found for transaction {transaction_id}")
                raise HTTPException(status_code=404, detail="No confident match found")

            conn.commit()

            return {
                "message": "Transaction added and matched successfully", 
                "transaction_id": transaction_id,
                "brand_name": best_match["brand_name"],
                "confidence_score": best_score,
                "brand_category": best_match["category"],
                "brand_website": best_match["website"],
                "brand_country": best_match["country"]
            }

        except Exception as e:
            conn.rollback()
            logging.error(f"Error adding transaction: {e}")
            raise HTTPException(status_code=500, detail=f"Error adding transaction: {e}")
        finally:
            release_db_conn(conn)
    else:
        logging.error("Failed to connect to the database")
        raise HTTPException(status_code=500, detail="Failed to connect to the database")