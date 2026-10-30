# 中项网项目查询 MCP

为 AI 助手提供中项网会员项目查询能力。服务在本机运行，检查并尝试复用上次登录状态；需要重新登录时，由用户在专用 Chrome 窗口完成操作，再按当前需求查询项目。

本仓库从原有 Skill 升级为 **Python MCP 服务 + 配套 Skill**，仓库地址保持不变。MCP 负责浏览器与数据获取，Skill 提供查询流程。服务采用本地 stdio 连接，不提供远程 HTTP 地址。

## 工作流程

1. AI 根据当前请求确定查询词，调用 `check_login`。
2. 登录有效时继续；需要登录时调用 `open_login`。
3. 用户在专用 Chrome 输入账号、密码及验证码，完成后告知 AI。
4. AI 再检查登录状态，调用 `search_projects` 并整理结果。

启动服务、检查登录和打开登录窗口均不会搜索项目。搜索必须提供非空关键词，不使用历史查询词作为默认值。登录状态由网站决定是否继续有效，不能保证长期免登录。

## 环境与安装

需要 Python 3.10+、已安装的 Google Chrome、可访问中项网的网络以及具有相应权限的会员账号。浏览器以可见窗口运行，需要本地桌面环境。目前主要在 Windows 验证。

```shell
git clone https://github.com/Jinguji-Tamamo/ccpc-projects-skill.git
cd ccpc-projects-skill
python -m venv .venv
```

Windows 安装依赖：

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS / Linux 安装依赖：

```shell
.venv/bin/python -m pip install -r requirements.txt
```

程序使用本机 Chrome，无需另外下载 Playwright Chromium。依赖为官方 MCP Python SDK 1.x 与 Playwright。

## 配置 MCP

在支持本地 stdio MCP 的客户端中添加服务。以下是通用 JSON 示例，也可参考 `mcp-config.example.json`；不同客户端的配置入口及字段可能有所不同。

```json
{
  "mcpServers": {
    "ccpc-projects": {
      "command": "C:/tools/ccpc-projects-skill/.venv/Scripts/python.exe",
      "args": ["C:/tools/ccpc-projects-skill/ccpc_mcp.py"],
      "env": {"CCPC_DATA_DIR": "C:/private/ccpc-data"}
    }
  }
}
```

将路径替换为实际安装位置。`command` 必须指向安装过依赖的 Python；macOS / Linux 使用 `.venv/bin/python` 的绝对路径。`CCPC_DATA_DIR` 可省略，默认数据目录为 `~/.ccpc-projects`。

客户端会启动并管理服务，无需预先运行程序。手动运行 `python ccpc_mcp.py` 时，终端等待 MCP 协议输入而没有业务输出属于正常现象。不要向标准输出添加普通日志，以免破坏通信。

连接成功后，应能看到下面三个工具。可以向 AI 提出：

> 查询安义县与再生资源利用有关的项目，先列出候选项目，需要登录时提示我操作。

## MCP 工具

| 工具 | 参数 | 用途 |
| --- | --- | --- |
| `check_login` | 无 | 打开或复用专用 Chrome，检查登录，不搜索 |
| `open_login` | 无 | 显示手动登录窗口，立即返回，不阻塞等待 |
| `search_projects` | `keyword` 必填；`limit` 默认 20，范围 1–50 | 检查认证后按关键词查询，仅获取首页 |

用户完成登录后，AI 应再调用 `check_login`，不要连续循环检查。搜索发现认证失效时只返回状态，不自动输入凭据。`limit` 仅限制首页返回条数，不会触发分页。

成功查询返回 `status: ok`、`keyword`、`page`、`total`、`returned` 和 `projects`。`total` 是网站报告的总数，不代表已读取全部项目。

| 状态 | 含义 |
| --- | --- |
| `authenticated` | 已识别到登录后的页面 |
| `needs_login` | 显示登录表单，或查询接口返回认证失效 |
| `waiting_for_user` | 窗口已打开，等待用户手动登录 |
| `unknown` | 无法确认登录，可能是网络、加载速度或网站改版问题 |
| `invalid_argument` | 查询词为空或返回数量超出范围 |
| `query_rejected` | 网站拒绝查询，需检查权限或验证提示 |
| `unexpected_response` | 查询响应结构变化 |
| `error` | 浏览器或网络操作未完成 |

## 本地登录状态与数据

数据目录下 `private_profile/` 保存专用 Chrome 配置，包含 Cookie 和其他登录数据。普通 Chrome 与此配置相互独立，日常浏览器中登录不会自动同步到服务。

浏览器操作在独立线程中顺序执行，服务退出时关闭浏览器并保留配置。同一数据目录只运行一个服务。旧版测试程序用户可以将 `CCPC_DATA_DIR` 指向原来 `private_profile` 所在的父目录，程序仍会重新检查登录状态。

MCP 将项目数据直接返回客户端，不自动写入结果文件。仓库不含账号密码、Cookie、token、浏览器配置或会员查询结果；服务不向 AI 返回认证请求头。账号密码和验证码由用户在页面输入，访问范围取决于账号权限。

## Skill 与命令行

仅配置 MCP 即可使用。如需统一 AI 的查询流程，可将本仓库放入个人 skills 目录，文件夹命名为 `ccpc-projects`，加载根目录 `SKILL.md`。

命令行入口保留，调用相同后端：

```shell
python scripts/search.py check
python scripts/search.py login
python scripts/search.py search --keyword "本次查询词"
```

命令行登录需用户完成后按 Enter，再检查状态并退出；MCP 的 `open_login` 无需终端输入。命令行搜索直接输出 JSON，不再生成旧版结果文件。认证有效或搜索成功返回退出码 0，其余业务状态返回 2。不要与 MCP 同时使用同一数据目录。

## 验证与限制

原 Python 方案已实测浏览器搜索及查询接口返回数据。MCP 协议测试位于 `tests/test_protocol.py`，验证连接、工具发现、必填参数和无效参数不会触发查询；运行 `python tests/test_protocol.py` 即可复查，无需登录。

当前仅查询搜索首页，未实现自动分页、项目详情读取，以及独立地区、日期、行业筛选参数。AI 需核对结果地区与业务相关性。长期会话复用尚未验证成功；网站主动使会话失效或更改页面结构时，可能需要重新登录或更新程序。

项目政策资格须另查现行官方文件，不能仅凭关键词认定符合中央资金条件。

## 常见问题

**客户端无法启动服务**：检查 Python、脚本是否使用绝对路径，并确认该 Python 环境已经安装依赖。

**找不到 Chrome 或配置被占用**：确认已安装 Google Chrome，关闭使用相同配置目录的其他测试程序或服务后重试。

**登录后仍不能查询**：调用 `check_login` 查看状态，检查页面和账号权限。`unknown` 只表示检查失败，不一定是登录过期。

**换电脑后要求重新登录**：登录配置仅保存在本机，不随仓库分发。新环境需要用户重新登录。
