from fastapi import APIRouter, HTTPException
from db import get_db_conn, release_db_conn
from embeddings import generate_brand_embedding

brand_router = APIRouter()

@brand_router.post("/regenerate-brand-embeddings")
def regenerate_brand_embeddings():
    conn = get_db_conn()
    if conn:
        try:
            cur = conn.cursor()

            cur.execute("UPDATE brands SET embedding = NULL WHERE embedding IS NOT NULL")
            conn.commit()

            cur.execute("SELECT id, name, category, website, country FROM brands WHERE embedding IS NULL")
            brands = cur.fetchall()

            if not brands:
                return {"message": "No brands to regenerate embeddings for"}

            for brand in brands:
                brand_id = brand[0]
                name = brand[1]
                category = brand[2]
                website = brand[3]
                country = brand[4]

                embedding = generate_brand_embedding(name, category, website, country)

                if embedding:
                    cur.execute("UPDATE brands SET embedding = %s WHERE id = %s", (embedding, brand_id))

            conn.commit()
            return {"message": "Brand embeddings regenerated successfully"}

        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error regenerating brand embeddings: {e}")
        finally:
            release_db_conn(conn)
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to the database")
