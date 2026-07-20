import csv
from pathlib import Path
from typing import List, Optional

from app.shared.schemas import DocumentMatch, Transaction


def load_transactions(data_dir: Path) -> List[Transaction]:
    with (data_dir / "transactions.csv").open(newline="", encoding="utf-8") as handle:
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


def load_documents(data_dir: Path) -> List[str]:
    text = (data_dir / "documents.txt").read_text(encoding="utf-8")
    return [part.strip() for part in text.split("\n\n") if part.strip()]


def filter_transactions(
    transactions: List[Transaction],
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Transaction]:
    filtered = transactions
    if category:
        filtered = [t for t in filtered if t.category.lower() == category.lower()]
    if date_from:
        filtered = [t for t in filtered if t.date >= date_from]
    if date_to:
        filtered = [t for t in filtered if t.date <= date_to]
    return filtered


def search_documents(documents: List[str], query: str) -> List[DocumentMatch]:
    query = query.lower()
    matches: List[DocumentMatch] = []
    for document in documents:
        if query in document.lower():
            snippet = document.split("\n")[-1][:180]
            matches.append(DocumentMatch(source=document.split(":")[0], snippet=snippet, score=1.0))
    return matches
