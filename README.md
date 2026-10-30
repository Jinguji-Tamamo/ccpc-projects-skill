# 中项网项目查询 Skill

为 AI 助手提供中项网会员项目查询能力。用户在专用浏览器中完成登录后，程序尝试复用本机保存的登录状态，并根据每次提出的需求查询项目；登录状态失效时，再由用户手动登录。

本项目采用 Python 和 Playwright 实现，以 Skill 形式提供使用流程和查询脚本。目前未封装为 MCP 服务。

## 工作方式

1. 检查上次保存的登录状态，确认是否仍能访问登录后的页面。
2. 状态有效时继续查询；无法确认时，提示用户在专用 Chrome 窗口完成登录。
3. 根据用户当前请求确定关键词，执行搜索。
4. 获取搜索响应，再使用 Python 直接请求同一个只读查询接口，将结果保存为 JSON 文件。

程序没有默认搜索词。`check` 和 `login` 均不执行项目搜索；只有明确运行 `search --keyword` 才会发起查询。账号、密码和验证码由用户在网站页面中输入。

## 环境要求

- Python 3.10 或更高版本
- 已安装的 Google Chrome
- 可正常访问中项网的网络环境
- 具备相应项目访问权限的中项网账号

目前已在 Windows 环境下验证浏览器搜索及 Python 接口查询。其他系统尚未实测。

## 安装

### 作为 Python 工具使用

下载或克隆仓库，进入仓库目录后安装依赖：

```shell
git clone https://github.com/Jinguji-Tamamo/ccpc-projects-skill.git
cd ccpc-projects-skill
python -m pip install -r requirements.txt
```

程序使用电脑中已经安装的 Chrome，无需另外下载 Playwright Chromium。

以下命令均在仓库根目录执行。如果系统使用 `python3` 或 Windows 的 `py` 命令，请相应替换示例中的 `python`。

### 作为 Codex Skill 使用

将仓库放入个人 skills 目录，文件夹命名为 `ccpc-projects`，并安装依赖。常见目录结构为：

```text
~/.codex/skills/ccpc-projects/
├── SKILL.md
├── README.md
├── requirements.txt
└── scripts/
    └── search.py
```

其中 `~` 表示当前用户的主目录；Windows 通常为 `C:\Users\你的用户名`。安装后，在能够加载该 Skill 的聊天中使用：

> 使用 $ccpc-projects，查询安义县与再生资源利用相关的项目，先列出候选项目和投资额。

Skill 会先确定本次查询范围，再检查登录状态。关键词搜索结果仍需由 AI 结合地区、建设内容等信息筛选；复杂条件并非都已实现为脚本参数。

## 使用步骤

### 1. 检查登录状态

```shell
python scripts/search.py check
```

检查在后台进行，不执行项目搜索。

| 输出 | 含义 | 后续操作 |
| --- | --- | --- |
| `SESSION_REUSED` | 已识别到登录后的页面 | 可以按需搜索 |
| `NEEDS_LOGIN` | 未能确认登录有效，退出码为 2 | 运行登录命令并检查页面 |

登录检查依赖网页显示。网络异常、页面加载缓慢或网站改版也可能导致检查失败，因此 `NEEDS_LOGIN` 不一定意味着账号已退出。

### 2. 按需手动登录

```shell
python scripts/search.py login
```

程序会打开专用 Chrome 窗口。若上次登录仍有效，会直接结束；否则等待用户输入账号、密码及验证码，最长等待 10 分钟。登录成功后关闭窗口并保留浏览器配置。

专用浏览器与日常使用的 Chrome 配置相互独立。在普通 Chrome 中登录，不代表本程序已经登录。请勿同时运行多个命令使用同一份专用配置。

### 3. 按当前需求搜索

```shell
python scripts/search.py search --keyword "本次查询关键词"
```

`--keyword` 为必填参数，不填写或仅输入空白字符时，程序会报错退出。

搜索命令也会检查登录状态；如无法确认有效登录，会等待用户手动登录，成功后继续本次查询。

## 输出与本地数据

默认数据目录为 `~/.ccpc-projects`：

| 路径 | 内容 |
| --- | --- |
| `private_profile/` | 专用 Chrome 配置，包含 Cookie 等登录状态 |
| `search_result.json` | 浏览器搜索接口返回的原始数据 |
| `python_direct_result.json` | Python 直接请求相同查询接口返回的数据 |
| `tmp/` | 程序运行所需的临时文件 |

查询成功后，可从 JSON 中的 `data.list` 读取项目列表。具体字段以网站当次响应为准。结果文件会被后续成功查询覆盖，需保留历史记录时请自行另存。

可通过环境变量 `CCPC_DATA_DIR` 更换数据目录，例如在 PowerShell 中：

```powershell
$env:CCPC_DATA_DIR = "D:\ccpc-data"
python scripts/search.py check
```

登录状态及会员查询数据仅保存在本机，不应提交到 GitHub 或随 Skill 分发。本仓库不包含账号密码、Cookie、token 或项目查询结果。

## 当前能力与限制

- 已验证：用户手动登录后，Python 可完成浏览器搜索，并通过相同查询接口获取结构化结果。
- 当前仅处理搜索首页，不自动遍历分页，也未实现项目详情批量读取。
- 脚本目前仅提供关键词参数，尚未提供地区、时间、行业及项目阶段等独立筛选参数。
- 长期登录状态复用尚未验证成功。网站也可能主动使会话失效，届时需要重新登录。
- 查询权限取决于账号和网站规则。程序不会绕过验证码、会员权限或其他访问限制。
- 项目信息不能直接证明符合某项资金申报条件。涉及中央预算内投资等政策判断时，应另行核对现行政策、项目建设内容及前期手续。

## 常见问题

**为什么每次都提示登录？**

先确认是否使用了同一个数据目录。如果更换了 `CCPC_DATA_DIR`、运行用户或电脑，程序可能无法找到原来的浏览器配置。也可能是网站使会话失效，或登录检查未能识别页面；请运行 `login` 查看实际状态。

**提示找不到 Playwright 或 Chrome，怎么办？**

在运行脚本的同一 Python 环境中执行 `python -m pip install -r requirements.txt`，并确认电脑已安装 Google Chrome。

**浏览器配置被占用，怎么办？**

关闭此前由本程序启动的专用 Chrome 窗口，确认没有其他查询进程正在使用同一数据目录后再试。无需清理日常 Chrome 的登录数据。

**页面超时或接口返回失败，怎么办？**

检查网络、登录状态和账号权限。如果网页本身可以正常查询，脚本仍持续失败，可能需要更新页面定位方式或接口匹配规则。错误退出时，不应将数据目录中此前留下的结果文件当作本次查询结果。
