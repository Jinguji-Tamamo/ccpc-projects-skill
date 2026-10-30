"""Local stdio MCP server. Authentication material never leaves the browser profile."""
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

class BrowserService:
    def __init__(self):
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.playwright = self.context = self.page = None
        self.root = Path(os.environ.get('CCPC_DATA_DIR', str(Path.home() / '.ccpc-projects'))).resolve()

    async def call(self, action, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.pool, self.execute, action, *args)

    def ensure_browser(self):
        if self.context is not None:
            try:
                if self.page.is_closed():
                    self.page = self.context.new_page()
                return
            except Exception:
                self.close()
        from playwright.sync_api import sync_playwright
        self.root.mkdir(parents=True, exist_ok=True)
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            str(self.root / 'private_profile'), channel='chrome', headless=False,
            viewport={'width': 1440, 'height': 1000})
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

    def session_status(self):
        from playwright.sync_api import TimeoutError
        self.page.goto('https://vip.ccpc360.com/#/dashboard', wait_until='domcontentloaded', timeout=45000)
        try:
            self.page.get_by_text('数据更新至', exact=False).first.wait_for(timeout=15000)
            return {'status': 'authenticated'}
        except TimeoutError:
            # A visible password input confirms a login screen. A slow/changed page does not.
            if self.page.locator('input[type="password"]').first.is_visible():
                return {'status': 'needs_login', 'message': '请调用 open_login，由用户在专用 Chrome 中手动登录。'}
            return {'status': 'unknown', 'message': '未能确认登录状态，请检查网络或打开登录窗口查看页面。'}

    def execute(self, action, *args):
        try:
            if action == 'close':
                self.close()
                return {'status': 'closed'}
            self.ensure_browser()
            if action == 'check':
                return self.session_status()
            if action == 'login':
                # Do not reload a login page while the user may be typing.
                if 'ccpc360.com' not in self.page.url:
                    self.page.goto('https://vip.ccpc360.com/#/dashboard', timeout=45000)
                self.page.bring_to_front()
                return {'status': 'waiting_for_user', 'message': '请在专用 Chrome 中完成登录；完成后调用 check_login。此操作不会搜索项目。'}
            if action == 'search':
                keyword, limit = args
                state = self.session_status()
                if state['status'] != 'authenticated':
                    return state
                self.page.goto('https://vip.ccpc360.com/#/projectQuery/searchItems', timeout=45000)
                field = self.page.get_by_placeholder("支持输入多个关键词，以'，'隔开").first
                field.wait_for(timeout=45000)
                field.fill(keyword)
                def matches(response):
                    from urllib.parse import urlsplit
                    parsed = urlsplit(response.url)
                    return parsed.hostname == 'java.ccpc360.com' and parsed.path in (
                        '/business-center-app-zxw-member/project-accurate/project-info-page',
                        '/business-center-app-zxw-member/fb/project/info-search/page-new')
                with self.page.expect_response(matches, timeout=60000) as pending:
                    self.page.get_by_role('button', name='搜 索').click()
                response = pending.value
                payload = response.json()
                if response.status in (401, 403) or payload.get('code') == 401:
                    return {'status': 'needs_login', 'message': '查询认证失效，请重新手动登录。'}
                if payload.get('success') is not True and payload.get('code') not in (0, 200):
                    return {'status': 'query_rejected', 'message': '网站拒绝查询，请检查账号权限或页面中的验证提示。'}
                data = payload.get('data')
                if not isinstance(data, dict) or not isinstance(data.get('list'), list):
                    return {'status': 'unexpected_response', 'message': '网站响应结构变化，未返回项目列表。'}
                return {'status': 'ok', 'keyword': keyword, 'page': 1,
                        'total': data.get('total'), 'returned': min(limit, len(data['list'])),
                        'projects': data['list'][:limit], 'scope': '仅搜索首页，未遍历分页或读取详情'}
            return {'status': 'invalid_action'}
        except Exception as exc:
            # Browser errors can contain request URLs or headers; do not return raw exceptions.
            return {'status': 'error', 'error_type': type(exc).__name__,
                    'message': '操作未完成，请检查网络、Chrome 安装及专用配置是否被其他进程占用。'}

    def close(self):
        try:
            if self.context:
                self.context.close()
        finally:
            if self.playwright:
                self.playwright.stop()
            self.context = self.page = self.playwright = None

service = BrowserService()

@asynccontextmanager
async def lifespan(app):
    try:
        yield {}
    finally:
        await service.call('close')
        service.pool.shutdown(wait=True)

mcp = FastMCP('ccpc-projects', lifespan=lifespan)

@mcp.tool()
async def check_login() -> dict[str, Any]:
    """检查本机保存的中项网登录状态；不搜索。会打开或复用专用 Chrome。"""
    return await service.call('check')

@mcp.tool()
async def open_login() -> dict[str, Any]:
    """打开专用 Chrome 让用户手动登录，立即返回；不输入密码、不解验证码、不搜索。"""
    return await service.call('login')

@mcp.tool()
async def search_projects(keyword: str, limit: int = 20) -> dict[str, Any]:
    """仅根据用户当前明确的关键词搜索中项网项目。失效时返回需登录，不自动登录；仅查询首页。"""
    if not keyword.strip():
        return {'status': 'invalid_argument', 'message': 'keyword 必须为用户本次明确的非空查询词。'}
    if not 1 <= limit <= 50:
        return {'status': 'invalid_argument', 'message': 'limit 必须在 1 到 50 之间。'}
    return await service.call('search', keyword.strip(), limit)

if __name__ == '__main__':
    mcp.run(transport='stdio')
