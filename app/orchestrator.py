from typing import Dict, List
import json
from urllib import request

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="HoldCo Orchestrator")

RETAIL_SERVICE_URL = "http://127.0.0.1:8001"
LOGISTICS_SERVICE_URL = "http://127.0.0.1:8002"


def call_json(url: str, payload: Dict | None = None) -> Dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
    with request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


class QuestionRequest(BaseModel):
    question: str


class OrchestratorResponse(BaseModel):
    subsidiaries: List[str]
    answer: str


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "orchestrator"}


@app.post("/answer", response_model=OrchestratorResponse)
def answer_question(request: QuestionRequest) -> OrchestratorResponse:
    question = request.question.lower()

    if "retail" in question:
        transactions = call_json(f"{RETAIL_SERVICE_URL}/transactions")
        answer = f"Retail has {len(transactions)} transactions in the current sample."
        return OrchestratorResponse(subsidiaries=["retail"], answer=answer)

    if "logistics" in question or "fuel" in question or "warehouse" in question or "transport" in question:
        transactions = call_json(f"{LOGISTICS_SERVICE_URL}/transactions")
        answer = f"Logistics has {len(transactions)} transactions in the current sample."
        return OrchestratorResponse(subsidiaries=["logistics"], answer=answer)

    if "transaction" in question or "expense" in question or "spend" in question or "travel" in question:
        retail_transactions = call_json(f"{RETAIL_SERVICE_URL}/transactions")
        logistics_transactions = call_json(f"{LOGISTICS_SERVICE_URL}/transactions")
        answer = (
            f"Retail has {len(retail_transactions)} transactions and logistics has {len(logistics_transactions)} transactions."
        )
        return OrchestratorResponse(subsidiaries=["retail", "logistics"], answer=answer)

    if "contract" in question or "document" in question or "report" in question or "vendor" in question:
        retail_matches = call_json(
            f"{RETAIL_SERVICE_URL}/documents/search",
            payload={"query": request.question},
        )
        logistics_matches = call_json(
            f"{LOGISTICS_SERVICE_URL}/documents/search",
            payload={"query": request.question},
        )
        answer = (
            f"Retail found {len(retail_matches)} relevant document match(es) and logistics found {len(logistics_matches)}."
        )
        return OrchestratorResponse(subsidiaries=["retail", "logistics"], answer=answer)

    return OrchestratorResponse(subsidiaries=["retail"], answer="I can help with retail and logistics transactions and document search.")
