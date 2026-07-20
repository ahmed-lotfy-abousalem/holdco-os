from typing import Any, Dict, List

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def list_tools(base_url: str) -> List[Dict[str, Any]]:
    async with streamablehttp_client(f"{base_url}/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.list_tools()
            return [
                {"name": tool.name, "description": tool.description, "inputSchema": tool.inputSchema}
                for tool in response.tools
            ]


async def call_tool(base_url: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
    async with streamablehttp_client(f"{base_url}/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            if result.isError:
                raise RuntimeError(f"tool '{tool_name}' returned an error: {result.content}")
            if result.structuredContent is not None:
                return result.structuredContent.get("result", result.structuredContent)
            return [item.text for item in result.content]
