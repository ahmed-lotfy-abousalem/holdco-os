import pytest
from fastapi.testclient import TestClient

from app.subsidiaries.retail import service as retail_service
from app.subsidiaries.logistics import service as logistics_service
from app.subsidiaries.finance import service as finance_service

SERVICES = {
    "retail": retail_service,
    "logistics": logistics_service,
    "finance": finance_service,
}


@pytest.mark.parametrize("name,module", SERVICES.items())
def test_health(name, module):
    client = TestClient(module.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "subsidiary": name}


@pytest.mark.parametrize("name,module", SERVICES.items())
def test_transactions_endpoint_returns_rows(name, module):
    client = TestClient(module.app)
    response = client.get("/transactions")
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert all({"date", "amount", "category", "counterparty", "description"} <= row.keys() for row in results)


@pytest.mark.parametrize("name,module", SERVICES.items())
def test_transactions_filtered_by_category(name, module):
    client = TestClient(module.app)
    sample_category = client.get("/transactions").json()[0]["category"]
    response = client.get("/transactions", params={"category": sample_category})
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert all(row["category"].lower() == sample_category.lower() for row in results)


@pytest.mark.parametrize("name,module", SERVICES.items())
def test_transactions_filtered_by_date_range(name, module):
    client = TestClient(module.app)
    response = client.get("/transactions", params={"date_from": "2026-02-01", "date_to": "2026-02-28"})
    assert response.status_code == 200
    assert all("2026-02" in row["date"] for row in response.json())


@pytest.mark.parametrize("name,module", SERVICES.items())
def test_transactions_unknown_category_returns_empty(name, module):
    client = TestClient(module.app)
    response = client.get("/transactions", params={"category": "does_not_exist"})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("name,module", SERVICES.items())
def test_document_search_matches_known_term(name, module):
    client = TestClient(module.app)
    response = client.post("/documents/search", json={"query": "report"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    for match in results:
        assert "source" in match and "snippet" in match and "score" in match


@pytest.mark.parametrize("name,module", SERVICES.items())
def test_document_search_no_match_returns_empty(name, module):
    client = TestClient(module.app)
    response = client.post("/documents/search", json={"query": "nonexistent_term_xyz"})
    assert response.status_code == 200
    assert response.json() == []


def test_subsidiary_data_is_isolated():
    """Each subsidiary's REST API must only ever return its own data, never another's."""
    counterparties = {}
    for name, module in SERVICES.items():
        client = TestClient(module.app)
        rows = client.get("/transactions").json()
        counterparties[name] = {row["counterparty"] for row in rows}

    assert counterparties["retail"].isdisjoint(counterparties["finance"])
    assert counterparties["retail"].isdisjoint(counterparties["logistics"])
    assert counterparties["finance"].isdisjoint(counterparties["logistics"])
