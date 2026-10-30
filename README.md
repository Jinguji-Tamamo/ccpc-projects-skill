# 中项网项目查询 Skill

Python + Playwright 查询中项网会员项目信息。先复用本机登录状态，失效时由用户手动登录；只按用户当前需求搜索，没有默认关键词。

## 安装

需要 Python 3.10+、Google Chrome 和有访问权限的中项网账号。

```shell
python -m pip install -r requirements.txt
python scripts/search.py check
python scripts/search.py login
python scripts/search.py search --keyword "你的查询词"
```

将本仓库复制到 Codex 的个人 skills 目录，文件夹命名为 `ccpc-projects`，即可使用 skill。脚本命令须在仓库目录运行。

## 登录与数据

账号密码、验证码由用户在专用浏览器中输入。Cookie 和本地存储保存在 `~/.ccpc-projects/private_profile`，不会随仓库分发。设置 `CCPC_DATA_DIR` 可以更换数据目录。同一配置目录只运行一个进程。

`check` 不执行搜索；有效时输出 `SESSION_REUSED`，需要登录时输出 `NEEDS_LOGIN` 并返回退出码 2。`login` 也不会搜索。登录最长等待 10 分钟。

搜索结果保存为数据目录中的 `search_result.json` 和 `python_direct_result.json`，后者是 Python 重发观察到的只读查询请求所得结果。不得提交认证信息或会员查询数据。

## 当前验证范围

已实测 Python 浏览器搜索和直接接口查询成功。当前仅获取搜索首页，不自动遍历分页或读取项目详情；地区、时间等复杂筛选需继续开发。登录检查依赖网页显示，页面变化或网络故障可能导致无法确认登录，需要人工检查。尚未验证长期会话复用成功。项目政策资格须另行核对官方文件。
