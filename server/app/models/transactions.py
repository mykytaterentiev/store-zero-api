from pydantic import BaseModel

class Transaction(BaseModel):
    merchant_name: str
    city: str
    mcc: str
    country: str
