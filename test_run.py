import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json, time, requests

BASE_URL = "https://arudradey-qwen-image-2-1-uncensored-gguf.hf.space"
MCP_URL  = f"{BASE_URL}/gradio_api/mcp/"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

_session_id = None

def post_mcp(payload):
    hdrs = {**HEADERS}
    if _session_id:
        hdrs["Mcp-Session-Id"] = _session_id
    try:
        r = requests.post(MCP_URL, json=payload, headers=hdrs, timeout=30)
        print(f"  -> HTTP {r.status_code}")
        return r.json() if r.status_code == 200 else {"_raw": r.text[:300]}
    except Exception as e:
        return {"_error": str(e)}

# ── 1. Initialize ──────────────────────────────────────────────────────────────
print("="*55)
print("  Qwen MCP Connectivity Test")
print("="*55)
print(f"  URL: {MCP_URL}\n")

print("[1] MCP initialize ...")
resp = post_mcp({
    "jsonrpc":"2.0","id":1,"method":"initialize",
    "params":{
        "protocolVersion":"2024-11-05",
        "capabilities":{},
        "clientInfo":{"name":"qwen-test","version":"1.0"}
    }
})
print(f"  result: {json.dumps(resp, ensure_ascii=False)[:300]}")

# ── 2. List tools ──────────────────────────────────────────────────────────────
print("\n[2] tools/list ...")
resp2 = post_mcp({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
tools = resp2.get("result",{}).get("tools", [])
for t in tools:
    print(f"  - {t.get('name')}: {t.get('description','')[:70]}")
if not tools:
    print(f"  raw: {json.dumps(resp2, ensure_ascii=False)[:300]}")

# ── 3. Call generate ───────────────────────────────────────────────────────────
print("\n[3] tools/call: generate ...")
prompt = "What is the capital of France? Answer in one word."
resp3 = post_mcp({
    "jsonrpc":"2.0","id":3,"method":"tools/call",
    "params":{
        "name":"qwen_image_2_1_uncensored_gguf_generate",
        "arguments":{"message": prompt, "request": None, "mode":"text"}
    }
})
content = resp3.get("result",{}).get("content",[])
answer = None
for item in content:
    if item.get("type") == "text":
        answer = item.get("text","")
        break
print(f"  prompt : {prompt}")
print(f"  answer : {answer or json.dumps(resp3, ensure_ascii=False)[:300]}")

# ── 4. Gradio REST fallback ────────────────────────────────────────────────────
print("\n[4] Gradio REST fallback /gradio_api/call/generate ...")
try:
    r = requests.post(
        f"{BASE_URL}/gradio_api/call/generate",
        json={"data": ["Tell me a fun fact about the moon.", None, "text"]},
        headers={"Content-Type":"application/json"}, timeout=30
    )
    print(f"  HTTP {r.status_code}")
    event_id = r.json().get("event_id") if r.status_code == 200 else None
    print(f"  event_id: {event_id}")
    if event_id:
        sr = requests.get(
            f"{BASE_URL}/gradio_api/call/generate/{event_id}",
            stream=True, timeout=60,
            headers={"Accept":"text/event-stream"}
        )
        for line in sr.iter_lines(decode_unicode=True):
            if line:
                print(f"  stream> {line[:250]}")
                if '"success"' in line or '"complete"' in line:
                    break
except Exception as e:
    print(f"  Error: {e}")

print("\n[Done]")
