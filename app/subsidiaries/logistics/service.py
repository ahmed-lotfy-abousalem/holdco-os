from pathlib import Path

from app.shared.rest_factory import create_rest_app

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "logistics"

app = create_rest_app("logistics", DATA_DIR)
