from pydantic import BaseModel


class Transaction(BaseModel):
    date: str
    amount: float
    category: str
    counterparty: str
    description: str


class DocumentMatch(BaseModel):
    source: str
    snippet: str
    score: float


class DocumentSearchRequest(BaseModel):
    query: str
