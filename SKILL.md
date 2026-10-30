---
name: ccpc-projects
description: 使用 Python 查询中项网会员项目信息，复用本机登录状态；失效时让用户手动登录，再按用户当次需求搜索并整理项目。
---

# 中项网项目查询

运行 skill 目录中的 `scripts/search.py`，依赖见 `requirements.txt`。需要 Python 3.10+ 和本机 Google Chrome。首次安装运行 `python -m pip install -r requirements.txt`。运行数据默认保存在用户目录的 `.ccpc-projects`，可用 `CCPC_DATA_DIR` 指定。该目录含登录状态和查询结果，不能上传或提交 Git。

## 工作流程

1. 明确本次用户需求。关键词、地区、时间和数量从当前请求推导；关键范围不明确时询问。没有本次搜索需求，不运行搜索。不继承历史示例“安义”。
2. 先执行 `scripts/search.py check`。它复用专用浏览器配置并检查登录后的页面，不能仅凭 Cookie 文件存在认定有效。`SESSION_REUSED` 表示可继续；`NEEDS_LOGIN`（退出码 2）表示需登录。
3. 失效时执行 `scripts/search.py login`，告知用户在新开的专用 Chrome 窗口手动登录。程序最多等待 10 分钟；密码、短信和验证码由用户处理。登录命令不会搜索。用户曾在普通 Chrome 登录不意味着专用配置已登录。
4. 仅在用户给出查询需求后执行 `scripts/search.py search --keyword "本次关键词"`。该命令也会复核会话，失效时等待手动登录。不要同时启动多个命令使用同一配置目录。
5. 读取 `python_direct_result.json` 的 `data.list`，并检查成功状态、总数、地区和项目相关性。文件会覆盖，只代表本次首页结果，不声称已遍历全部分页或读取详情。需要更多页、细节或复杂地区筛选时，扩展脚本或使用已连接的浏览器可见筛选入口，并说明实际范围。
6. 搜索接口仅反映项目信息。涉及中央资金资格判断，另行核对现行官方政策，并区分“待核实线索”和“确认满足条件”。

程序在浏览器搜索后用 Python urllib 重发刚观察到的只读查询请求，保存结构化结果；不打印请求头、Cookie、token。认证依赖 token 请求头，不应假设仅 Cookie 即可调用接口。不绕过网站验证或账户权限，不自动收藏、导出付费数据或变更账号设置。

## 运行示例

PowerShell（替换关键词为本次请求，不自动执行示例）：

```shell
python scripts/search.py check
python scripts/search.py login
python scripts/search.py search --keyword "用户当次关键词"
```

网络或打开浏览器需要执行权限时按环境要求申请，不能通过关闭安全检查来重试。超时或登录拒绝时报告实际错误，不自动无限重试。
