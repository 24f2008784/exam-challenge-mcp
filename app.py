import hashlib
import os

from flask import Flask, jsonify, request, Response

app = Flask(__name__)

EMAIL = "24f2008784@ds.study.iitm.ac.in"
SERVER_NAME = "exam-challenge-mcp"
SERVER_VERSION = "1.0.0"
SUPPORTED_PROTOCOL_VERSIONS = {
    "2024-11-05",
    "2025-03-26",
    "2025-06-18",
}


def rpc_result(request_id, result):
    return jsonify({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    })


def rpc_error(request_id, code, message):
    return jsonify({
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    })


@app.route("/", methods=["GET", "POST"])
@app.route("/mcp", methods=["GET", "POST"])
def mcp_endpoint():
    if request.method == "GET":
        # Streamable HTTP clients may probe the endpoint. The grader's
        # required interaction uses JSON-RPC POST requests.
        return jsonify({
            "service": SERVER_NAME,
            "transport": "MCP Streamable HTTP",
            "endpoint": "/",
        })

    if not request.is_json:
        return rpc_error(None, -32700, "Expected an application/json JSON-RPC request"), 400

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return rpc_error(None, -32700, "Invalid JSON-RPC request"), 400

    method = payload.get("method")
    request_id = payload.get("id")
    params = payload.get("params") or {}

    # JSON-RPC notifications must not receive a JSON-RPC response.
    if method == "notifications/initialized" or (
        isinstance(method, str) and method.startswith("notifications/")
    ):
        return Response(status=202)

    if payload.get("jsonrpc") != "2.0" or not isinstance(method, str):
        return rpc_error(request_id, -32600, "Invalid Request"), 400

    if method == "initialize":
        requested_version = params.get("protocolVersion", "2025-03-26")
        protocol_version = (
            requested_version
            if requested_version in SUPPORTED_PROTOCOL_VERSIONS
            else "2025-03-26"
        )
        return rpc_result(request_id, {
            "protocolVersion": protocol_version,
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
            "instructions": "Call solve_challenge; the challenge is read from the HTTP request headers for each call.",
        })

    if method == "ping":
        return rpc_result(request_id, {})

    if method == "tools/list":
        return rpc_result(request_id, {
            "tools": [{
                "name": "solve_challenge",
                "description": "Compute the required SHA-256 challenge response using the per-call X-Exam-Challenge HTTP header and the registered exam email.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True,
                },
            }]
        })

    if method == "tools/call":
        tool_name = params.get("name")
        if tool_name != "solve_challenge":
            return rpc_error(request_id, -32602, "Unknown tool")

        # IMPORTANT: challenge comes from the current HTTP request headers,
        # never from params.arguments or the JSON body.
        challenge = request.headers.get("X-Exam-Challenge")
        if challenge is None:
            return rpc_result(request_id, {
                "content": [{"type": "text", "text": "Missing X-Exam-Challenge header"}],
                "isError": True,
            })

        normalized_email = EMAIL.strip().lower()
        answer = hashlib.sha256(
            f"{challenge}:{normalized_email}".encode("utf-8")
        ).hexdigest()[:16]

        return rpc_result(request_id, {
            "content": [{"type": "text", "text": answer}],
        })

    return rpc_error(request_id, -32601, "Method not found")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
