# AI 聊天后端（Flask + Render）

本项目接收前端消息，调用 OpenAI Responses API，再返回文字回答。前端使用独立 GitHub 仓库并部署到 GitHub Pages；后端使用本仓库并部署到 Render。

浏览器中的 GitHub Pages 前端 → Render 后端 `/api/chat` → OpenAI API → 后端返回 JSON → 前端显示回答。

代码尚未部署或真实调用 API。本机没有可用 Python 运行环境，尚未执行运行测试。

## 1. 上传后端代码

按课程截图要求，新建 **Public（公开）** 仓库，例如 `my-ai-chatbot-backend`，与前端仓库分开。

在 GitHub 点 `Add file → Upload files`，将以下文件上传到仓库根目录：

- `app.py`
- `requirements.txt`
- `.python-version`
- `.gitignore`
- `.env.example`（只有占位符）
- `README.md`
- `prompt_log.md`

不要上传外层 `houduan` 文件夹。`frontend-starter` 是给另一个前端仓库准备的材料，不属于后端仓库，已加入 `.gitignore`。GitHub 网页手动上传不会按 `.gitignore` 自动筛选，请按清单选择文件。不要上传真实密钥、口令或 `.env` 文件。

## 2. 部署 Render 后端

登录 https://dashboard.render.com ，点 `New + → Web Service`，连接并选择后端仓库。

| 设置 | 填写内容 |
| --- | --- |
| Name | `my-ai-chatbot-backend`，重名可改 |
| Language / Runtime | `Python 3` |
| Branch | `main`，以实际分支为准 |
| Root Directory | 留空 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 90` |
| Instance Type | 学习时可选 Free，以账户实际选项为准 |
| Health Check Path | `/health` |

在 Environment Variables 中添加以下配置，值两边不加引号：

| 变量 | 用途 / 示例 |
| --- | --- |
| `OPENAI_API_KEY` | 从 https://platform.openai.com/api-keys 创建的真实密钥，只放后端 |
| `OPENAI_MODEL` | `gpt-4.1-mini`，也是代码默认值 |
| `CHAT_PASSWORD` | 自己设置的随机英文数字口令，建议至少 20 位 |
| `FRONTEND_ORIGINS` | `https://你的GitHub用户名.github.io`，多个来源用英文逗号分隔 |

若前端页面是 `https://alice.github.io/my-ai-chatbot-frontend/`，`FRONTEND_ORIGINS` 填 `https://alice.github.io`，**不含仓库路径**。自定义域名则填写对应来源（协议 + 域名 + 非默认端口）。

检查价格和配置后点击 Deploy / Create Web Service。状态变成 Live 后，访问 `https://你的服务名.onrender.com/health`，应看到 `{"status":"ok"}`。根路径 `/` 显示服务信息，不再显示聊天页面。健康检查不会调用 OpenAI，也不表示密钥已验证。

## 3. 独立前端

已有前端仓库时，按下一节接口约定接入。没有前端时，可将本地 `frontend-starter` 目录中的文件上传到另一个仓库根目录，按其中 README 配置 GitHub Pages。前端 `config.js` 要填写真实 Render 后端网址。

| 仓库 | 部署平台 | 内容 |
| --- | --- | --- |
| `my-ai-chatbot-backend` | Render Web Service | Python 后端、依赖、README、提示日志 |
| `my-ai-chatbot-frontend` 或已有前端仓库 | GitHub Pages | HTML/CSS/JavaScript、公开的后端网址 |

## 4. 接口及前后端通信

### GET / 和 GET /health

无需口令。`/` 返回服务信息；`/health` 返回 HTTP 200 和 `{"status":"ok"}`，用于浏览器直接访问或 Render 健康检查。聊天前端不必调用这两个接口。

### POST /api/chat

用户点击发送时，前端调用完整地址，例如 `https://你的服务名.onrender.com/api/chat`。

请求头：

```text
Content-Type: application/json
X-Chat-Password: 用户在网页输入的访问口令
```

请求 JSON：

```json
{"messages":[{"role":"user","content":"你好"}]}
```

多轮对话按 `user`、`assistant` 交替排列，以 `user` 开始和结束。最多 21 条，每条最多 8000 字符，总计最多 24000 字符，请求体最多 64 KiB。示例前端每次最多携带最近 5 轮上下文，并按总长度进一步缩减。

成功返回 HTTP 200：

```json
{"reply":"你好！有什么可以帮你？"}
```

失败返回 `{"error":"可读的错误说明"}`：

| HTTP 状态码 | 含义 |
| --- | --- |
| 400 | 消息格式或长度不合要求 |
| 401 | 访问口令不正确 |
| 413 | 请求体太大 |
| 429 | OpenAI 额度不足或请求频率受限 |
| 502 | OpenAI 连接失败、调用失败或没有文字输出 |
| 503 | 后端未配置密钥或口令 |

前端等待时禁用发送按钮；成功后将 `reply` 作为纯文本显示并加入历史；失败显示 `error` 并保留输入。示例前端还设置了请求超时。

浏览器会先发送 `OPTIONS /api/chat` 跨域预检。Flask-CORS 自动为配置的来源处理预检，并允许 `Content-Type` 和 `X-Chat-Password` 请求头。未配置 `FRONTEND_ORIGINS` 时不允许跨域读取。CORS 不能替代口令验证，也不能阻止其他客户端直接调用接口。

## 5. 身份验证、密钥和数据

- OpenAI 密钥只从后端环境变量读取，不写在 GitHub、HTML 或前端 JavaScript 中。
- `CHAT_PASSWORD` 是学习项目的共享访问口令，由网页使用者输入，后端用常量时间比较验证。它不是 OpenAI 密钥，也不是完整用户账户系统。
- 课程展示如需口令，请私下提供给评阅者，不要放进公开 README。
- 后端没有数据库，不主动记录消息或口令。上下文由浏览器传入，刷新页面会清空示例前端的历史。
- OpenAI 请求设置 `store=False`，但不等同于零数据保留承诺。
- 当前版本用于个人学习或课程演示，没有按用户限流或总费用硬上限。API 调用会产生费用，请在 OpenAI 平台确认计费和用量。

## 6. 本地运行（可选）

云端部署不要求先安装本地 Python。若需本地开发，安装 Python 3.13，在后端目录打开 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:OPENAI_API_KEY = '只在自己的电脑填写真实密钥'
$env:OPENAI_MODEL = 'gpt-4.1-mini'
$env:CHAT_PASSWORD = '自己设置的随机访问口令'
$env:FRONTEND_ORIGINS = 'http://localhost:8000'
.\.venv\Scripts\python.exe app.py
```

后端地址为 `http://127.0.0.1:5000`。`.env.example` 只是示例，程序不会自动读取 `.env`。不要分享含密钥的终端历史。

本地前端：将前端 `config.js` 的后端地址临时改为 `http://127.0.0.1:5000`，在前端目录另开终端运行 `python -m http.server 8000`，浏览器访问 `http://localhost:8000`。发布前将 `config.js` 改回 Render HTTPS 地址。

## 7. 部署后检查与排错

1. 打开后端 `/health`，确认服务运行。
2. 打开 Pages 前端，用错误口令发送消息，确认出现口令错误提示。
3. 换成正确口令发送「你好」，确认收到真实回复。这一步会调用 API。
4. 发送「我上一句说了什么」，确认多轮对话连通。

- 无法连接后端：核对 `config.js` 和 `FRONTEND_ORIGINS`，特别检查来源不含仓库路径。修改环境变量后等待 Render 重新部署。
- Render 打开只有 JSON：正常，聊天页面在 GitHub Pages。
- Render 部署失败：查看 Logs，检查文件是否位于仓库根目录、启动命令是否正确。
- 首次请求慢：Render 免费服务闲置后会休眠，等待唤醒后重试。
- 额度或模型错误：检查 OpenAI Billing、Usage、Limits、密钥有效性及模型访问权限。
- 不要双击 HTML 用 `file://` 测试跨域；使用 Pages 或本地 HTTP 服务。

## 8. 提示日志及官方参考

AI 辅助开发记录见 [prompt_log.md](prompt_log.md)。

- OpenAI 入门：https://developers.openai.com/api/docs/quickstart
- Render Flask 部署：https://render.com/docs/deploy-flask
- Render 免费服务限制：https://render.com/docs/free
- Flask-CORS：https://flask-cors.readthedocs.io/en/latest/api.html
- GitHub Pages 发布：https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
