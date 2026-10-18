# Exam Challenge MCP Server

A minimal MCP Streamable HTTP server exposing exactly one tool: `solve_challenge`.

## Behavior

- Supports `initialize`, `notifications/initialized`, `tools/list`, `tools/call`, and `ping`.
- Reads `X-Exam-Challenge` from the HTTP headers on every tool call.
- Returns the first 16 lowercase hexadecimal characters of
  `SHA-256(challenge + ":" + "24f2008784@ds.study.iitm.ac.in")`.
- The tool input schema has no required properties.

## Deploy on Render

1. Create a GitHub repository, for example `exam-challenge-mcp`.
2. Upload `app.py`, `requirements.txt`, `Procfile`, and `render.yaml` to the repository root.
3. In Render, choose **New + → Blueprint** and connect that GitHub repository.
4. Render reads `render.yaml`; create the service and wait until it reports **Live**.
5. Your public endpoint will look like `https://YOUR-SERVICE-NAME.onrender.com/`. Submit that exact HTTPS URL.

You can also deploy it as a **Web Service** manually:
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 30`

## Quick local test

Install dependencies and run:

```bash
pip install -r requirements.txt
python app.py
```

Initialize:

```bash
curl -X POST http://127.0.0.1:8000/ -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-03-26\",\"capabilities\":{},\"clientInfo\":{\"name\":\"test\",\"version\":\"1.0\"}}}"
```

Call the tool with a sample challenge:

```bash
curl -X POST http://127.0.0.1:8000/ -H "Content-Type: application/json" -H "X-Exam-Challenge: 0123456789abcdef0123456789abcdef" -d "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"solve_challenge\",\"arguments\":{}}}"
```

The `X-Exam-Timestamp` and `X-Exam-Signature` headers are not required because signature verification is optional and unscored.
