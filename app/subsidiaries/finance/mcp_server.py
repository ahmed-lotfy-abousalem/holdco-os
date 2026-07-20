from pathlib import Path

from app.shared.mcp_factory import create_mcp_server

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "finance"

mcp = create_mcp_server("finance", DATA_DIR, port=9003)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
