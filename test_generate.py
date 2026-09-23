"""
test_generate.py — Generate gambar via Qwen Image 2.1 Uncensored MCP
Endpoint: /generate(prompt, mode, reference, aspect_ratio, steps, seed, randomize_seed)
"""
import sys, io, json, requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "https://arudradey-qwen-image-2-1-uncensored-gguf.hf.space"
MCP  = f"{BASE}/gradio_api/mcp/"
HDRS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

def mcp_post(method, params, req_id):
    r = requests.post(MCP, json={"jsonrpc":"2.0","id":req_id,"method":method,"params":params},
                      headers=HDRS, timeout=180, stream=True)
    raw = r.content.decode("utf-8", errors="replace")
    for line in raw.splitlines():
        if line.startswith("data:"):
            try: return json.loads(line[5:].strip())
            except: pass
    return {"_raw": raw[:500]}

# Initialize
print("[1] Initializing...")
mcp_post("initialize", {
    "protocolVersion": "2024-11-05", "capabilities": {},
    "clientInfo": {"name": "test", "version": "1.0"}
}, 1)
print("  OK")

# Generate
prompt = "A majestic white wolf standing on a snowy mountain peak at sunset, photorealistic"
print(f"[2] Generating image...")
print(f"    prompt: {prompt}")

resp = mcp_post("tools/call", {
    "name": "qwen_image_2_1_uncensored_gguf_generate",
    "arguments": {
        "prompt": prompt,
        "mode": "Create an image",
        "aspect_ratio": "Square \u00b7 1:1 (1024x1024)",
        "steps": 20,
        "seed": 42,
        "randomize_seed": True,
    }
}, 2)

result = resp.get("result", resp)
content = result.get("content", []) if isinstance(result, dict) else []
print(f"\n  isError: {result.get('isError', '?')}")
for item in content:
    if isinstance(item, dict):
        t = item.get("type")
        if t == "text":
            print(f"  [text] {item.get('text','')[:300]}")
        elif t == "image":
            print(f"  [image] url={item.get('url','')}")
            print(f"          data_len={len(item.get('data',''))}")
        else:
            print(f"  [{t}] {str(item)[:200]}")

if not content:
    print(f"  raw: {json.dumps(result, ensure_ascii=False)[:500]}")

print("\n[Done]")
