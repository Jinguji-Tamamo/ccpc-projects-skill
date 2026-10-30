"""Manual login, persistent local profile, then a Python project search."""
import sys
import json
import argparse
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(os.environ.get('CCPC_DATA_DIR', str(Path.home() / '.ccpc-projects'))).resolve()
(ROOT / 'tmp').mkdir(exist_ok=True)
os.environ['TEMP'] = str(ROOT / 'tmp')
os.environ['TMP'] = str(ROOT / 'tmp')
sys.path.insert(0, str(ROOT / 'deps'))
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('command', choices=['check', 'login', 'search'])
    ap.add_argument('--keyword', help='Required for search; no default query')
    args = ap.parse_args()
    if args.command == 'search' and not (args.keyword and args.keyword.strip()):
        ap.error('search requires an explicit --keyword')
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(ROOT / 'private_profile'), channel='chrome', headless=args.command == 'check',
            viewport={'width': 1440, 'height': 1000})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto('https://vip.ccpc360.com/#/dashboard')
        # Validate the server-backed account UI, rather than cookie existence.
        account = page.get_by_text('数据更新至', exact=False).first
        # Dashboard content is populated only after the authenticated route loads.
        try:
            account.wait_for(timeout=15000)
            print('SESSION_REUSED', flush=True)
        except PlaywrightTimeout:
            if args.command == 'check':
                print('NEEDS_LOGIN', flush=True)
                ctx.close()
                return 2
            print('WAITING_FOR_USER_LOGIN: 请在专用 Chrome 窗口完成登录；程序不会填写密码或验证码。', flush=True)
            account.wait_for(timeout=600000)
            print('LOGIN_CONFIRMED', flush=True)
        if args.command in ('check', 'login'):
            ctx.close()
            return 0
        page.goto('https://vip.ccpc360.com/#/projectQuery/searchItems')
        field = page.get_by_placeholder("支持输入多个关键词，以'，'隔开").first
        field.wait_for(timeout=60000)
        field.fill(args.keyword)
        with page.expect_response(lambda r: 'java.ccpc360.com' in r.url and
                ('project-info-page' in r.url or 'info-search/page-new' in r.url), timeout=90000) as pending:
            page.get_by_role('button', name='搜 索').click()
        response = pending.value
        data = response.json()
        if data.get('success') is not True and data.get('code') not in (0, 200):
            raise RuntimeError('Search rejected; no successful result saved. Please check login or account permissions.')
        (ROOT / 'search_result.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        # Reissue only this observed, read-only search request with Python urllib.
        import urllib.request
        req = response.request
        headers = {k: v for k,v in req.all_headers().items()
                   if k.lower() not in {'host','content-length','accept-encoding','connection'}
                   and not k.startswith(':')}
        body = req.post_data_buffer
        direct = urllib.request.Request(req.url, data=body, headers=headers, method=req.method)
        with urllib.request.urlopen(direct, timeout=60) as result:
            direct_data = json.loads(result.read())
        if direct_data.get('success') is not True and direct_data.get('code') not in (0, 200):
            raise RuntimeError('Direct query rejected; browser result is available, direct API is not validated.')
        (ROOT / 'python_direct_result.json').write_text(json.dumps(direct_data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'http_status': response.status, 'endpoint': urlsplit(req.url).path,
                          'direct_code': direct_data.get('code'), 'direct_success': direct_data.get('success'),
                          'result_file': str(ROOT / 'python_direct_result.json')}, ensure_ascii=False), flush=True)
        ctx.close()

if __name__ == '__main__':
    sys.exit(main() or 0)
