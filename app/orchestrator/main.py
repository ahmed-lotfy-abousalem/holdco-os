import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.orchestrator import mcp_client

load_dotenv()

app = FastAPI(title="HoldCo Orchestrator")

STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/", response_class=HTMLResponse)
def chat_ui() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")

SUBSIDIARY_MCP_URLS = {
    "retail": "http://127.0.0.1:9001",
    "logistics": "http://127.0.0.1:9002",
    "finance": "http://127.0.0.1:9003",
}

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))
MAX_TOOL_ITERATIONS = 5

SYSTEM_PROMPT = (
    "You are the HoldCo OS assistant for a holding company with three subsidiaries: retail, logistics, "
    "and finance. Use the available tools to look up their transactions or documents. Tool names are "
    "prefixed with the subsidiary they belong to (e.g. 'finance__get_transactions'). Only call tools for "
    "subsidiaries that are actually relevant to the question. If a tool result reports a subsidiary as "
    "unavailable, say so in your answer instead of guessing at its data. If the question has nothing to "
    "do with subsidiary transactions or documents, answer directly without calling any tools.\n\n"
    "When calling a get_transactions tool, never guess a category value. Call it with no category filter "
    "first to see the real categories present in the results, and only add a category filter afterward if "
    "you need to narrow down to one you actually observed. A filtered call that returns zero results does "
    "not necessarily mean there is no data — prefer the unfiltered result when summarizing totals.\n\n"
    "If the user asks what you can do, what tools or data you have access to, or otherwise asks about your "
    "own capabilities, describe them in plain language (you can look up transactions and search documents "
    "for retail, logistics, and finance) — do not call any tools just to answer a question about yourself."
)


async def discover_tools() -> tuple[List[Dict], List[str]]:
    """Ask every subsidiary's MCP server what tools it offers. Returns (ollama_tool_schemas, unavailable)."""

    async def discover_one(subsidiary: str, base_url: str):
        try:
            return subsidiary, await mcp_client.list_tools(base_url), None
        except Exception:
            return subsidiary, [], subsidiary

    discovered = await asyncio.gather(
        *(discover_one(name, url) for name, url in SUBSIDIARY_MCP_URLS.items())
    )

    ollama_tools: List[Dict] = []
    unavailable: List[str] = []
    for subsidiary, tools, failed in discovered:
        if failed:
            unavailable.append(failed)
            continue
        for tool in tools:
            ollama_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": f"{subsidiary}__{tool['name']}",
                        "description": f"[{subsidiary}] {tool['description']}",
                        "parameters": tool["inputSchema"],
                    },
                }
            )
    return ollama_tools, unavailable


async def call_qualified_tool(qualified_name: str, arguments: Dict) -> Dict:
    """Call a tool named like 'finance__get_transactions' on the right subsidiary's MCP server."""
    subsidiary, _, tool_name = qualified_name.partition("__")
    if not tool_name or subsidiary not in SUBSIDIARY_MCP_URLS:
        return {"error": f"unknown tool '{qualified_name}'"}
    try:
        result = await mcp_client.call_tool(SUBSIDIARY_MCP_URLS[subsidiary], tool_name, arguments)
        return {"subsidiary": subsidiary, "result": result}
    except Exception:
        return {"subsidiary": subsidiary, "error": f"{subsidiary} service is currently unavailable"}


async def ollama_chat(messages: List[Dict], tools: List[Dict]) -> Dict:
    payload = {"model": OLLAMA_MODEL, "messages": messages, "tools": tools, "stream": False}
    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_SECONDS) as client:
        response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()["message"]


class QuestionRequest(BaseModel):
    question: str


class OrchestratorResponse(BaseModel):
    subsidiaries: List[str]
    answer: str
    unavailable: List[str] = []


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "orchestrator"}


@app.post("/answer", response_model=OrchestratorResponse)
async def answer_question(request: QuestionRequest) -> OrchestratorResponse:
    tools, unavailable = await discover_tools()
    messages: List[Dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.question},
    ]
    touched: List[str] = []

    try:
        for _ in range(MAX_TOOL_ITERATIONS):
            message = await ollama_chat(messages, tools)
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                return OrchestratorResponse(
                    subsidiaries=sorted(set(touched)),
                    answer=(message.get("content") or "").strip(),
                    unavailable=sorted(set(unavailable)),
                )

            messages.append(message)
            for call in tool_calls:
                function = call["function"]
                tool_result = await call_qualified_tool(function["name"], function.get("arguments") or {})

                subsidiary = tool_result.get("subsidiary")
                if subsidiary:
                    touched.append(subsidiary)
                    if "error" in tool_result:
                        unavailable.append(subsidiary)

                messages.append({"role": "tool", "content": json.dumps(tool_result)})
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="local LLM (Ollama) is unavailable") from exc

    return OrchestratorResponse(
        subsidiaries=sorted(set(touched)),
        answer="I wasn't able to finish gathering the information in time.",
        unavailable=sorted(set(unavailable)),
    )
