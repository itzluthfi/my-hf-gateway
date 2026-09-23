"""
test_final.py — Full working test untuk Qwen Image 2.1 Uncensored MCP
Server returns SSE format: "event: message\r\ndata: {...}\r\n\r\n"
"""
import sys, io, json, requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "https://arudradey-qwen-image-2-1-uncensored-gguf.hf.space"
MCP  = f"{BASE}/gradio_api/mcp/"
HDRS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

_session_id = None

def mcp_post(method: str, params: dict, req_id: int) -> dict:
    """POST ke MCP, parse SSE response jadi dict."""
    hdrs = {**HDRS}
    if _session_id:
        hdrs["Mcp-Session-Id"] = _session_id
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    r = requests.post(MCP, json=payload, headers=hdrs, timeout=120, stream=True)
    raw = r.content.decode("utf-8", errors="replace")
    # Parse SSE: ambil baris "data: {json}"
    for line in raw.splitlines():
        if line.startswith("data:"):
            try:
                return json.loads(line[5:].strip())
            except Exception:
                pass
    return {"_raw": raw[:400], "_status": r.status_code}


def sep(s):
    print(f"\n{'─'*54}\n  {s}\n{'─'*54}")


# ── 1. Initialize ──────────────────────────────────────────────────────────────
sep("1. MCP Initialize")
resp = mcp_post("initialize", {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "qwen-mcp-client", "version": "1.0"},
}, req_id=1)
print(f"  serverInfo: {resp.get('result', {}).get('serverInfo', resp)}")


# ── 2. List tools ──────────────────────────────────────────────────────────────
sep("2. tools/list")
resp2 = mcp_post("tools/list", {}, req_id=2)
tools = resp2.get("result", {}).get("tools", [])
for t in tools:
    print(f"  • {t['name']}")
    desc = t.get("description","")
    if desc:
        print(f"    {desc[:90]}")
print(f"  Total: {len(tools)} tool(s)")


# ── 3. update_ui_mode ─────────────────────────────────────────────────────────
sep("3. tools/call: update_ui_mode -> 'Create an image'")
resp3 = mcp_post("tools/call", {
    "name": "qwen_image_2_1_uncensored_gguf_update_ui_mode",
    "arguments": {"selected_mode": "Create an image"},
}, req_id=3)
print(f"  result: {json.dumps(resp3.get('result', resp3), ensure_ascii=False)[:200]}")


# ── 4. Generate (text mode) ────────────────────────────────────────────────────
sep("4. tools/call: generate (text mode)")
prompt = "What is the capital of France? Answer in exactly one word."
print(f"  prompt: {prompt}")

resp4 = mcp_post("tools/call", {
    "name": "qwen_image_2_1_uncensored_gguf_generate",
    "arguments": {
        "message": prompt,
        "request": None,
        "mode": "Create an image",
    },
}, req_id=4)

result4 = resp4.get("result", resp4)
content = result4.get("content", []) if isinstance(result4, dict) else []
answer = None
for item in content:
    if isinstance(item, dict) and item.get("type") == "text":
        answer = item.get("text", "")
        break

print(f"  answer: {answer or json.dumps(result4, ensure_ascii=False)[:400]}")


# ── 5. Cek /gradio_api/info (endpoints) ───────────────────────────────────────
sep("5. Gradio /gradio_api/info - Named Endpoints")
try:
    r = requests.get(f"{BASE}/gradio_api/info", timeout=10)
    info = r.json()
    named = info.get("named_endpoints", {})
    for name, detail in named.items():
        params = [p.get("parameter_name","?") for p in detail.get("parameters",[])]
        returns = [p.get("python_type",{}).get("type","?") for p in detail.get("returns",[])]
        print(f"  {name}({', '.join(params)}) -> {', '.join(returns)}")
except Exception as e:
    print(f"  Error: {e}")


print("\n[SELESAI] Semua test selesai.")
