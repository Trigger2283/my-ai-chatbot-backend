"""个人试用版 AI 聊天服务。密钥只从服务器环境变量读取。"""

import os
import re
import secrets

from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024

# 来源仅包含协议、域名和端口，不含 GitHub 仓库路径。
allowed_origins = [
    re.compile(re.escape(origin.strip().rstrip("/")) + r"\Z")
    for origin in os.environ.get("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]
CORS(
    app,
    resources={r"/api/.*": {"origins": allowed_origins}},
    methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Chat-Password"],
    supports_credentials=False,
)


@app.get("/")
def index():
    return jsonify(service="AI Chat Backend", health="/health", chat="/api/chat")


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.errorhandler(413)
def too_large(error):
    return jsonify(error="消息太长，请缩短后重试。"), 413


@app.post("/api/chat")
def chat():
    password = os.environ.get("CHAT_PASSWORD", "")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not password or not api_key:
        return jsonify(error="请先在 Render 配置 OPENAI_API_KEY 和 CHAT_PASSWORD。"), 503

    provided = request.headers.get("X-Chat-Password", "")
    if not secrets.compare_digest(provided.encode(), password.encode()):
        return jsonify(error="访问口令不正确。请输入你在 Render 设置的 CHAT_PASSWORD。"), 401

    body = request.get_json(silent=True)
    messages = body.get("messages") if isinstance(body, dict) else None
    if not isinstance(messages, list) or not 1 <= len(messages) <= 21:
        return jsonify(error="请发送 1 至 21 条有效消息。"), 400

    clean = []
    for index, message in enumerate(messages):
        expected_role = "user" if index % 2 == 0 else "assistant"
        if not isinstance(message, dict) or message.get("role") != expected_role:
            return jsonify(error="对话格式不正确，请开始新对话。"), 400
        content = message.get("content")
        if not isinstance(content, str) or not content.strip() or len(content) > 8000:
            return jsonify(error="每条消息需要包含 1 至 8000 个字符。"), 400
        clean.append({"role": expected_role, "content": content.strip()})

    if clean[-1]["role"] != "user" or sum(len(m["content"]) for m in clean) > 24000:
        return jsonify(error="对话太长或格式不正确，请开始新对话。"), 400

    try:
        with OpenAI(api_key=api_key, timeout=45.0, max_retries=0) as client:
            response = client.responses.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
                instructions="你是一位友好、耐心的 AI 助手。默认使用简体中文，解释清楚，回答简洁。",
                input=clean,
                max_output_tokens=1200,
                store=False,
            )
        reply = response.output_text
        if not reply:
            return jsonify(error="这次没有收到文字回复，请重试。"), 502
        return jsonify(reply=reply)
    except RateLimitError:
        return jsonify(error="API 额度不足或请求过于频繁，请检查 OpenAI 账户用量后重试。"), 429
    except APIConnectionError:
        return jsonify(error="连接 OpenAI 超时或失败，请稍后重试。"), 502
    except APIStatusError as error:
        app.logger.warning("OpenAI request failed with HTTP %s", error.status_code)
        return jsonify(error="OpenAI 调用失败，请检查 API 密钥、账户及模型权限。"), 502


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
