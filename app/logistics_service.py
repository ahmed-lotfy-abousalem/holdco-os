import csv
from pathlib import Path
from typing import List, Dict, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "logistics"

app = FastAPI(title="Logistics Subsidiary Service")


class DocumentSearchRequest(BaseModel):
    query: str


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


def load_transactions() -> List[Transaction]:
    with (DATA_DIR / "transactions.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        Transaction(
            date=row["date"],
            amount=float(row["amount"]),
            category=row["category"],
            counterparty=row["counterparty"],
            description=row["description"],
        )
        for row in rows
    ]


def load_documents() -> List[str]:
    text = (DATA_DIR / "documents.txt").read_text(encoding="utf-8")
    return [part.strip() for part in text.split("\n\n") if part.strip()]


TRANSACTIONS = load_transactions()
DOCUMENTS = load_documents()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "subsidiary": "logistics"}


@app.get("/transactions", response_model=List[Transaction])
def get_transactions(
    category: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
) -> List[Transaction]:
    filtered = TRANSACTIONS
    if category:
        filtered = [t for t in filtered if t.category.lower() == category.lower()]
    if date_from:
        filtered = [t for t in filtered if t.date >= date_from]
    if date_to:
        filtered = [t for t in filtered if t.date <= date_to]
    return filtered


@app.post("/documents/search", response_model=List[DocumentMatch])
def search_documents(request: DocumentSearchRequest) -> List[DocumentMatch]:
    query = request.query.lower()
    matches: List[DocumentMatch] = []
    for document in DOCUMENTS:
        if query in document.lower():
            snippet = document.split("\n")[-1][:180]
            matches.append(DocumentMatch(source=document.split(":")[0], snippet=snippet, score=1.0))
    return matches
