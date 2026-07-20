from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, Query

from app.shared.schemas import DocumentMatch, DocumentSearchRequest, Transaction
from app.shared.data import filter_transactions, load_documents, load_transactions, search_documents


def create_rest_app(name: str, data_dir: Path) -> FastAPI:
    """Build the REST API for one subsidiary. Kept for manual testing (curl, /docs)."""
    app = FastAPI(title=f"{name.title()} Subsidiary Service")

    transactions = load_transactions(data_dir)
    documents = load_documents(data_dir)

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok", "subsidiary": name}

    @app.get("/transactions", response_model=List[Transaction])
    def get_transactions(
        category: Optional[str] = Query(default=None),
        date_from: Optional[str] = Query(default=None),
        date_to: Optional[str] = Query(default=None),
    ) -> List[Transaction]:
        return filter_transactions(transactions, category, date_from, date_to)

    @app.post("/documents/search", response_model=List[DocumentMatch])
    def search(request: DocumentSearchRequest) -> List[DocumentMatch]:
        return search_documents(documents, request.query)

    return app
