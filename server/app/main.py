from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import transactions, brands, locations, table 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

app.include_router(transactions.transaction_router)
app.include_router(brands.brand_router)
app.include_router(locations.location_router)
app.include_router(table.table_router) 

@app.get("/")
def read_root():
    return {"message": "Connected to PostgreSQL!"}
