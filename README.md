# After Hours — AI Bar & Kitchen Backend

After Hours is a conversational AI host for a fictional late-night bar and kitchen. It shares cocktail ideas, cooking techniques, food pairings, and casual conversation with a warm, lightly humorous personality.

This repository contains the Flask backend. The English-language chat interface is maintained separately in the portfolio repository and hosted on GitHub Pages.

## Live application

- **Chat:** https://trigger2283.github.io/chatbot/
- **Backend:** https://my-ai-chatbot-backend-gevf.onrender.com
- **Health check:** https://my-ai-chatbot-backend-gevf.onrender.com/health
- **Frontend repository:** https://github.com/Trigger2283/Trigger2283.github.io
- **Backend repository:** https://github.com/Trigger2283/my-ai-chatbot-backend

The chat requires an access password provided by the site owner. This password is separate from the OpenAI API key.

## How it works

```text
GitHub Pages frontend
    | POST /api/chat: messages + access password
    v
Flask backend on Render
    | Server-side API key + role instructions + conversation
    v
OpenAI Responses API
    | Generated text
    v
Backend JSON response -> frontend conversation view
```

The frontend sends a request when the visitor clicks Send or presses Enter. The backend validates the access password and message format, calls OpenAI, and returns the reply. The frontend displays the reply as plain text. While a request is pending, it disables the send controls; on failure, it shows an English message based on the HTTP status and preserves the visitor's input for retrying.

The frontend includes up to five recent complete exchanges, followed by the current message. It may include fewer exchanges to stay within the character limit. Conversation history is held in browser memory and cleared on refresh or when starting a new conversation.

## Technology

- Python and Flask for HTTP endpoints
- Flask-CORS for browser cross-origin access
- OpenAI Python SDK and Responses API for text generation
- Gunicorn for serving the application on Render
- HTML, CSS, and JavaScript for the separate frontend

Dependencies are listed in `requirements.txt`; the Python version is specified in `.python-version`.

## Repository files

| File | Purpose |
| --- | --- |
| `app.py` | API routes, input validation, access control, CORS, and character instructions |
| `requirements.txt` | Python dependencies |
| `.python-version` | Python runtime version |
| `.env.example` | Configuration examples containing placeholders only |
| `.gitignore` | Excludes local secrets, virtual environments, and generated files |
| `README.md` | Setup, API, and operation documentation |
| `prompt.txt` | English record of user prompts from the initial development conversation; maintained separately from the runtime character instructions |

## Configuration

Set these environment variables on the backend:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI API key for a project with access to the selected model. Required for chat. |
| `OPENAI_MODEL` | Model ID. The current deployment is configured to use `gpt-6-luna`. If omitted, the code falls back to `gpt-4.1-mini`; it does not automatically select an accessible model. |
| `CHAT_PASSWORD` | Shared access password. Required for chat. Use a long, randomly generated value and share it privately. |
| `FRONTEND_ORIGINS` | Comma-separated browser origins allowed to read chat responses. For the deployed frontend, use `https://trigger2283.github.io`. |

When entering values in Render, do not add surrounding quotation marks.

An origin includes the scheme, hostname, and a non-default port if applicable. It does not include a folder or filename. For `https://trigger2283.github.io/chatbot/`, the allowed origin is `https://trigger2283.github.io`.

`.env.example` is a reference only. The application does not automatically load `.env` files.

## Deploy on Render

Create a Web Service connected to the backend repository with these settings:

| Setting | Value |
| --- | --- |
| Language | Python 3 |
| Branch | `main` |
| Root Directory | Leave blank when `app.py` is in the repository root |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 90` |
| Health Check Path | `/health` |

Add the environment variables, select an instance plan, and deploy. Once the service is live, check `/health` and test an actual conversation from the frontend. A successful health check confirms that the server is running; it does not validate the API key, model access, or available API quota.

After changing backend files, commit and push them to the connected branch. If automatic deployment is enabled, Render builds the update. Otherwise, deploy the latest commit manually. Confirm the deployment succeeds before testing new behavior.

## Run locally

Install Python 3.13. In a PowerShell terminal opened in the backend repository:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:OPENAI_API_KEY = 'YOUR_OPENAI_API_KEY'
$env:OPENAI_MODEL = 'gpt-6-luna'
$env:CHAT_PASSWORD = 'YOUR_RANDOM_CHAT_PASSWORD'
$env:FRONTEND_ORIGINS = 'http://localhost:8000'
.\.venv\Scripts\python.exe app.py
```

The local backend runs at `http://127.0.0.1:5000`. Gunicorn is used on Render; the command above uses Flask's development server locally. Do not share terminal history containing credentials.

To test the frontend locally, temporarily set its `chatbot/config.js` backend URL to `http://127.0.0.1:5000`. From the frontend repository root, run `python -m http.server 8000`, then open `http://localhost:8000/chatbot/`. Restore the production backend URL before publishing.

Open the frontend through an HTTP server or GitHub Pages. Opening an HTML file directly with `file://` does not produce the configured browser origin.

## API reference

### GET /

Returns basic service information. No password is required.

```json
{"service":"AI Chat Backend","health":"/health","chat":"/api/chat"}
```

### GET /health

Returns HTTP 200 with the service status and character-prompt version. No password is required, and no OpenAI request is made.

```json
{"status":"ok","prompt_version":"after-hours-v4"}
```

The version label identifies the prompt revision declared in `app.py` and can help confirm which revision is deployed.

### POST /api/chat

Request headers:

```text
Content-Type: application/json
X-Chat-Password: YOUR_CHAT_PASSWORD
```

Request body:

```json
{
  "messages": [
    {"role": "user", "content": "What would you mix for me tonight?"}
  ]
}
```

For multiple turns, send alternating `user` and `assistant` messages, beginning and ending with `user`. Only these roles are accepted; character instructions are supplied separately by the backend.

Request limits:

- 1–21 messages
- At most 8,000 characters per message, including whitespace
- At most 24,000 characters across the trimmed message contents
- At most 64 KiB for the complete request body

Each message must contain a string with at least one non-whitespace character. The 8,000-character limit is applied before trimming, including any whitespace.

Successful response, HTTP 200:

```json
{"reply":"Something crisp or something cozy?"}
```

Handled failures return an `error` field with a readable explanation. Backend explanations are currently in Chinese; the frontend maps HTTP status codes to English interface messages.

| HTTP status | Meaning |
| --- | --- |
| 400 | Invalid message structure or content length |
| 401 | Incorrect or missing chat password |
| 413 | Request body too large |
| 429 | OpenAI request limit or quota issue |
| 502 | OpenAI connection or API failure, or no text reply |
| 503 | Missing server-side API key or chat password |

### OPTIONS /api/chat

Flask and Flask-CORS handle browser preflight requests. Configured origins may use `POST` with the `Content-Type` and `X-Chat-Password` headers. No cross-origin browser access is allowed when `FRONTEND_ORIGINS` is empty.

## Character behavior

`BOT_INSTRUCTIONS` in `app.py` defines the After Hours host. It is sent with every chat request, independently of conversation history.

The host defaults to English, follows the language of the current user request, and maintains a relaxed bar-owner voice. It can explain recipes and techniques or engage in casual conversation. It has no live weather, browsing, reservations, or ordering tools. Its bar persona is fictional.

To change the character, edit `BOT_INSTRUCTIONS`, update `PROMPT_VERSION`, and deploy the backend. Start a new conversation to evaluate the revised prompt without earlier replies influencing the result. Model responses are variable; instructions guide behavior but do not guarantee identical phrasing or perfect consistency.

## Security and data handling

- Keep the OpenAI API key in backend environment variables. Never put it in frontend code, a public repository, screenshots, or the development prompt record.
- `CHAT_PASSWORD` provides shared-password access control, not individual user accounts. The backend verifies it before requesting an OpenAI response.
- CORS controls what browser origins can read responses. It does not stop direct requests from other clients and is not a substitute for authentication.
- The application has no per-user rate limiting, password-attempt limit, or application-level spending cap. Anyone with the chat password can make requests that consume API usage.
- The backend has no database and does not intentionally log message contents or passwords. Messages are sent to OpenAI for processing. `store=False` is set, but this is not a zero-data-retention guarantee.
- `.gitignore` helps prevent accidental Git tracking of local secret files. It does not remove already committed credentials, and manually uploading files on GitHub requires checking the selected files yourself.
- If a key is exposed, revoke it and replace the Render environment variable with a new key. Deleting the visible file alone does not invalidate the leaked key.

## Verification and troubleshooting

1. Open `/health` and confirm the expected `prompt_version`.
2. Test an incorrect chat password and confirm the frontend shows an access error.
3. Send a short message with the correct password to verify the complete API flow. This consumes API usage.
4. Send a follow-up to check conversation context and language continuity.

| Symptom | What to check |
| --- | --- |
| Old frontend appearance | Confirm the latest GitHub Pages deployment completed, then hard-refresh or use a fresh browser session. |
| Old character behavior | Confirm the latest Render deployment and `/health` version, then start a new conversation. |
| Cannot reach the backend | Check the frontend backend URL, network access, and `FRONTEND_ORIGINS`. Use the hosted webpage rather than a local HTML file. |
| First request is slow | A free Render instance may need to wake after being idle. |
| API or quota error | Check the configured model, project permissions, key validity, and OpenAI usage or billing status. |
| Deployment failed | Review Render logs, dependency installation, repository root, and the start command. |
| Backend root shows JSON | Expected: the chat interface is hosted separately on GitHub Pages. |

## Development record

The English user-prompt record is maintained in `prompt.txt`. It documents an earlier portion of development and is not automatically updated with subsequent changes. Runtime character instructions are maintained separately in `app.py`.

## References

- [OpenAI API quickstart](https://developers.openai.com/api/docs/quickstart)
- [Deploy Flask on Render](https://render.com/docs/deploy-flask)
- [Render free instances](https://render.com/docs/free)
- [Flask-CORS documentation](https://flask-cors.readthedocs.io/en/latest/api.html)
- [GitHub Pages publishing configuration](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
