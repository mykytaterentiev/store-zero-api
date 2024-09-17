from fastapi import APIRouter, HTTPException
from db import get_db_conn, release_db_conn

table_router = APIRouter()

@table_router.get("/transactions")
def get_transactions():
    conn = get_db_conn()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, merchant_name, city, mcc, country, brand_name, confidence_score FROM transactions")
            transactions = cur.fetchall()
            return {"transactions": transactions}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching transactions: {e}")
        finally:
            release_db_conn(conn)
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to the database")
