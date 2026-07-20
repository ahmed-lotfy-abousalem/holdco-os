from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from app.shared.data import filter_transactions, load_documents, load_transactions
from app.shared.data import search_documents as search_documents_in


def create_mcp_server(name: str, data_dir: Path, port: int) -> FastMCP:
    """Build the MCP server for one subsidiary. This is what the orchestrator's LLM actually calls."""
    mcp = FastMCP(name=f"{name}-subsidiary", host="127.0.0.1", port=port, stateless_http=True)

    transactions = load_transactions(data_dir)
    documents = load_documents(data_dir)

    @mcp.tool(name="get_transactions")
    def get_transactions_tool(
        category: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None
    ) -> list[dict]:
        """Get this subsidiary's transactions, optionally filtered by exact category or date range."""
        return [t.model_dump() for t in filter_transactions(transactions, category, date_from, date_to)]

    @mcp.tool(name="search_documents")
    def search_documents_tool(query: str) -> list[dict]:
        """Search this subsidiary's documents (contracts, reports, notes) for a query string."""
        return [m.model_dump() for m in search_documents_in(documents, query)]

    return mcp
