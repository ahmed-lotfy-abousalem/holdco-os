import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app.orchestrator import main as orchestrator

client = TestClient(orchestrator.app)

TOOL_SCHEMA = {"type": "object", "properties": {}}

FAKE_TOOLS = {
    orchestrator.SUBSIDIARY_MCP_URLS["retail"]: [
        {"name": "get_transactions", "description": "retail transactions", "inputSchema": TOOL_SCHEMA},
        {"name": "search_documents", "description": "retail documents", "inputSchema": TOOL_SCHEMA},
    ],
    orchestrator.SUBSIDIARY_MCP_URLS["logistics"]: [
        {"name": "get_transactions", "description": "logistics transactions", "inputSchema": TOOL_SCHEMA},
        {"name": "search_documents", "description": "logistics documents", "inputSchema": TOOL_SCHEMA},
    ],
    orchestrator.SUBSIDIARY_MCP_URLS["finance"]: [
        {"name": "get_transactions", "description": "finance transactions", "inputSchema": TOOL_SCHEMA},
        {"name": "search_documents", "description": "finance documents", "inputSchema": TOOL_SCHEMA},
    ],
}

FAKE_RESULTS = {
    (orchestrator.SUBSIDIARY_MCP_URLS["retail"], "get_transactions"): [{"id": 1}, {"id": 2}, {"id": 3}],
    (orchestrator.SUBSIDIARY_MCP_URLS["logistics"], "get_transactions"): [{"id": 1}, {"id": 2}],
    (orchestrator.SUBSIDIARY_MCP_URLS["finance"], "get_transactions"): [{"id": 1}],
    (orchestrator.SUBSIDIARY_MCP_URLS["finance"], "search_documents"): [{"source": "Document 3"}],
}


async def fake_list_tools(base_url):
    return FAKE_TOOLS[base_url]


async def fake_call_tool(base_url, tool_name, arguments):
    return FAKE_RESULTS[(base_url, tool_name)]


@pytest.fixture(autouse=True)
def stub_mcp_client(monkeypatch):
    monkeypatch.setattr(orchestrator.mcp_client, "list_tools", fake_list_tools)
    monkeypatch.setattr(orchestrator.mcp_client, "call_tool", fake_call_tool)


def tool_call_message(qualified_name, arguments):
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"function": {"name": qualified_name, "arguments": arguments}}],
    }


def final_message(content):
    return {"role": "assistant", "content": content}


def scripted_chat(monkeypatch, responses):
    queue = list(responses)

    async def scripted(messages, tools):
        if not queue:
            raise AssertionError("ollama_chat called more times than the test scripted")
        return queue.pop(0)

    monkeypatch.setattr(orchestrator, "ollama_chat", scripted)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "orchestrator"}


def test_chat_ui_is_served_at_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<title>HoldCo OS Chat</title>" in response.text


def test_discover_tools_prefixes_names_by_subsidiary():
    tools, unavailable = asyncio.run(orchestrator.discover_tools())
    names = {t["function"]["name"] for t in tools}
    assert names == {
        "retail__get_transactions",
        "retail__search_documents",
        "logistics__get_transactions",
        "logistics__search_documents",
        "finance__get_transactions",
        "finance__search_documents",
    }
    assert unavailable == []


def test_discover_tools_skips_unreachable_subsidiary(monkeypatch):
    async def flaky_list_tools(base_url):
        if base_url == orchestrator.SUBSIDIARY_MCP_URLS["finance"]:
            raise ConnectionError("refused")
        return FAKE_TOOLS[base_url]

    monkeypatch.setattr(orchestrator.mcp_client, "list_tools", flaky_list_tools)
    tools, unavailable = asyncio.run(orchestrator.discover_tools())

    assert unavailable == ["finance"]
    assert all(not t["function"]["name"].startswith("finance__") for t in tools)


def test_call_qualified_tool_unknown_subsidiary():
    result = asyncio.run(orchestrator.call_qualified_tool("nope__get_transactions", {}))
    assert "error" in result


def test_call_qualified_tool_malformed_name():
    result = asyncio.run(orchestrator.call_qualified_tool("not_qualified", {}))
    assert "error" in result


def test_llm_calls_a_tool_then_answers(monkeypatch):
    scripted_chat(
        monkeypatch,
        [
            tool_call_message("retail__get_transactions", {}),
            final_message("Retail has 3 transactions."),
        ],
    )
    response = client.post("/answer", json={"question": "How many retail transactions do we have?"})
    body = response.json()

    assert response.status_code == 200
    assert body["subsidiaries"] == ["retail"]
    assert body["answer"] == "Retail has 3 transactions."
    assert body["unavailable"] == []


def test_llm_calls_multiple_tools_and_aggregates_subsidiaries(monkeypatch):
    scripted_chat(
        monkeypatch,
        [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "retail__get_transactions", "arguments": {}}},
                    {"function": {"name": "logistics__get_transactions", "arguments": {}}},
                ],
            },
            final_message("Retail has 3 transactions and logistics has 2."),
        ],
    )
    response = client.post("/answer", json={"question": "What is our total spend across the company?"})
    body = response.json()

    assert body["subsidiaries"] == ["logistics", "retail"]
    assert body["unavailable"] == []


def test_llm_answers_directly_without_tools(monkeypatch):
    scripted_chat(
        monkeypatch,
        [final_message("I can only help with retail, logistics, and finance data.")],
    )
    response = client.post("/answer", json={"question": "What's the weather today?"})
    body = response.json()

    assert body["subsidiaries"] == []
    assert body["unavailable"] == []
    assert "retail, logistics, and finance" in body["answer"]


def test_document_search_tool_call(monkeypatch):
    scripted_chat(
        monkeypatch,
        [
            tool_call_message("finance__search_documents", {"query": "audit"}),
            final_message("Finance found one relevant document."),
        ],
    )
    response = client.post("/answer", json={"question": "Any recent audit reports?"})
    body = response.json()

    assert body["subsidiaries"] == ["finance"]
    assert body["answer"] == "Finance found one relevant document."


def test_degrades_gracefully_when_tool_target_is_down(monkeypatch):
    async def flaky_call_tool(base_url, tool_name, arguments):
        if base_url == orchestrator.SUBSIDIARY_MCP_URLS["finance"]:
            raise ConnectionError("refused")
        return FAKE_RESULTS[(base_url, tool_name)]

    monkeypatch.setattr(orchestrator.mcp_client, "call_tool", flaky_call_tool)
    scripted_chat(
        monkeypatch,
        [
            tool_call_message("finance__get_transactions", {}),
            final_message("Finance data is currently unavailable."),
        ],
    )

    response = client.post("/answer", json={"question": "Any recent loan activity?"})
    body = response.json()

    assert response.status_code == 200
    assert body["subsidiaries"] == ["finance"]
    assert body["unavailable"] == ["finance"]


def test_stops_after_max_tool_iterations(monkeypatch):
    async def always_calls_a_tool(messages, tools):
        return tool_call_message("retail__get_transactions", {})

    monkeypatch.setattr(orchestrator, "ollama_chat", always_calls_a_tool)

    response = client.post("/answer", json={"question": "How many retail transactions do we have?"})
    body = response.json()

    assert response.status_code == 200
    assert "wasn't able to finish" in body["answer"]


def test_ollama_unavailable_returns_503(monkeypatch):
    async def broken_chat(messages, tools):
        raise httpx.HTTPError("connection refused")

    monkeypatch.setattr(orchestrator, "ollama_chat", broken_chat)

    response = client.post("/answer", json={"question": "How many retail transactions do we have?"})
    assert response.status_code == 503
