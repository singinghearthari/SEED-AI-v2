"""Quick smoke test for SEED AI MCP Server."""
import sys, asyncio
sys.path.insert(0, "mcp_server")

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "mcp_server/server.py", "--transport", "stdio"]
    )
    async with stdio_client(params) as (read, write):
        from mcp import ClientSession
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            print(f"Tools registered: {len(result.tools)}")
            for t in result.tools:
                print(f"  - {t.name}")

            result2 = await session.list_resources()
            print(f"\nResources registered: {len(result2.resources)}")
            for r in result2.resources:
                print(f"  - {r.uri}")

            resp = await session.call_tool("get_disease_info", {"query": "tomato"})
            for c in resp.content:
                if hasattr(c, "text"):
                    lines = c.text.strip().split("\n")
                    print(f"\n'get_disease_info(tomato)' -> {len(lines)} lines")
                    print(f"  First disease: {lines[1]}")

            resp2 = await session.call_tool("get_treatment_plan", {"disease_name": "Early Blight"})
            for c in resp2.content:
                if hasattr(c, "text"):
                    lines = c.text.strip().split("\n")
                    count = len([l for l in lines if l.startswith("-")])
                    print(f"'get_treatment_plan(Early Blight)' -> {count} treatments found")

            resp3 = await session.call_tool("get_crop_guide", {"crop_name": "rice"})
            for c in resp3.content:
                if hasattr(c, "text"):
                    print(f"'get_crop_guide(rice)' -> {c.text.split(chr(10))[0]}")

    print("\nAll tests passed!")

asyncio.run(main())
