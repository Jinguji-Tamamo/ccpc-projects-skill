"""Exercise the real stdio protocol without opening a browser or searching."""
import asyncio
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server = Path(__file__).resolve().parents[1] / 'ccpc_mcp.py'
    params = StdioServerParameters(command=sys.executable, args=[str(server)], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            tools = (await client.list_tools()).tools
            assert {t.name for t in tools} == {'check_login', 'open_login', 'search_projects'}
            schema = next(t for t in tools if t.name == 'search_projects').inputSchema
            assert 'keyword' in schema['required']
            empty = await client.call_tool('search_projects', {'keyword': ' '})
            assert empty.structuredContent['status'] == 'invalid_argument'
            invalid = await client.call_tool('search_projects', {'keyword': 'test', 'limit': 0})
            assert invalid.structuredContent['status'] == 'invalid_argument'
            missing = await client.call_tool('search_projects', {})
            assert missing.isError
    print('PASS: stdio initialization, tool discovery, argument validation; no browser or search')

if __name__ == '__main__':
    asyncio.run(main())
