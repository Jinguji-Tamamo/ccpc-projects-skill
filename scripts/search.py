"""Optional CLI using the MCP backend."""
import argparse
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ccpc_mcp import service, check_login, open_login, search_projects

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['check', 'login', 'search'])
    parser.add_argument('--keyword')
    args = parser.parse_args()
    if args.command == 'search' and not (args.keyword and args.keyword.strip()):
        parser.error('search requires --keyword')
    try:
        if args.command == 'login':
            print(json.dumps(await open_login(), ensure_ascii=False), flush=True)
            await asyncio.to_thread(input, '完成手动登录后按 Enter 保存并退出：')
            result = await check_login()
        elif args.command == 'check':
            result = await check_login()
        else:
            result = await search_projects(args.keyword)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['status'] in ('ok', 'authenticated') else 2
    finally:
        await service.call('close')
        service.pool.shutdown(wait=True)

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
