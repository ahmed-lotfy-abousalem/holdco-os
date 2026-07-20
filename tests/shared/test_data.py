from pathlib import Path

from app.shared.data import filter_transactions, load_documents, load_transactions, search_documents

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


def test_load_transactions_reads_csv_rows():
    transactions = load_transactions(DATA_ROOT / "retail")
    assert len(transactions) > 0
    assert all(hasattr(t, "date") and hasattr(t, "amount") for t in transactions)


def test_load_documents_splits_on_blank_lines():
    documents = load_documents(DATA_ROOT / "retail")
    assert len(documents) == 3
    assert documents[0].startswith("Document 1")


def test_filter_transactions_by_category_is_case_insensitive():
    transactions = load_transactions(DATA_ROOT / "retail")
    filtered = filter_transactions(transactions, category="TRAVEL")
    assert len(filtered) > 0
    assert all(t.category == "travel" for t in filtered)


def test_filter_transactions_by_date_range():
    transactions = load_transactions(DATA_ROOT / "retail")
    filtered = filter_transactions(transactions, date_from="2026-02-01", date_to="2026-02-28")
    assert all("2026-02" in t.date for t in filtered)


def test_filter_transactions_unknown_category_returns_empty():
    transactions = load_transactions(DATA_ROOT / "retail")
    assert filter_transactions(transactions, category="does_not_exist") == []


def test_search_documents_matches_known_term():
    documents = load_documents(DATA_ROOT / "finance")
    matches = search_documents(documents, "audit")
    assert len(matches) > 0
    assert all(m.score == 1.0 for m in matches)


def test_search_documents_no_match_returns_empty():
    documents = load_documents(DATA_ROOT / "finance")
    assert search_documents(documents, "nonexistent_term_xyz") == []
