"""
test_qwen38.py — Test MCP koneksi & chat untuk Qwen3.8-27B-Uncensored-Demo
URL: https://jonathancoletti-qwen3-8-27b-uncensored-demo.hf.space/gradio_api/mcp/
"""
import sys, io, json, requests, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "https://jonathancoletti-qwen3-8-27b-uncensored-demo.hf.space"
MCP  = f"{BASE}/gradio_api/mcp/"
HDRS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

def mcp_post(method, params, req_id):
    r = requests.post(MCP, json={"jsonrpc":"2.0","id":req_id,"method":method,"params":params},
                      headers=HDRS, timeout=120, stream=True)
    raw = r.content.decode("utf-8", errors="replace")
    for line in raw.splitlines():
        if line.startswith("data:"):
            try: return json.loads(line[5:].strip())
            except: pass
    return {"_raw": raw[:500]}

print("==================================================")
print(" 1. Init MCP: Qwen3.8-27B-Uncensored")
print("==================================================")
init_res = mcp_post("initialize", {
    "protocolVersion": "2024-11-05", "capabilities": {},
    "clientInfo": {"name": "test-client", "version": "1.0"}
}, 1)
print(f"Server Info: {init_res.get('result', {}).get('serverInfo', init_res)}")

print("\n==================================================")
print(" 2. Tools List")
print("==================================================")
tools_res = mcp_post("tools/list", {}, 2)
tools = tools_res.get("result", {}).get("tools", [])
for t in tools:
    print(f"• Tool: {t['name']}")
    print(f"  Input Schema: {json.dumps(t.get('inputSchema', {}), indent=2)}")

print("\n==================================================")
print(" 3. Tes Chat / Respond")
print("==================================================")
prompt = "Halo! Siapa kamu dan apa kelebihanmu? Jawab singkat saja dalam 2 kalimat bahasa Indonesia."
print(f"Prompt: {prompt}\nMemproses response...")

t0 = time.time()
chat_res = mcp_post("tools/call", {
    "name": "Qwen3_8_27B_Uncensored_Demo_respond",
    "arguments": {
        "message": {
            "text": prompt,
            "files": []
        },
        "reasoning": "off",
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 20
    }
}, 3)
elapsed = time.time() - t0

print(f"Waktu respon: {elapsed:.2f}s")
print(f"Hasil: {json.dumps(chat_res.get('result', chat_res), ensure_ascii=False, indent=2)}")
