"""
test_run2.py — Gradio native API test untuk Qwen Image 2.1 Uncensored
Strategi: pakai /gradio_api/info untuk cek status, lalu /run/predict atau SSE poll yang benar.
"""
import sys, io, json, time, requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "https://arudradey-qwen-image-2-1-uncensored-gguf.hf.space"

def sep(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print("="*55)

# ── 1. Cek info space (apakah running?) ───────────────────────────────────────
sep("1. Cek Space Status (/gradio_api/info)")
try:
    r = requests.get(f"{BASE}/gradio_api/info", timeout=15)
    print(f"  HTTP {r.status_code}")
    if r.status_code == 200:
        info = r.json()
        print(json.dumps(info, indent=2, ensure_ascii=False)[:600])
    else:
        print(f"  body: {r.text[:300]}")
except Exception as e:
    print(f"  Error: {e}")

# ── 2. Cek /info Gradio biasa ─────────────────────────────────────────────────
sep("2. Cek /info endpoint")
try:
    r = requests.get(f"{BASE}/info", timeout=15)
    print(f"  HTTP {r.status_code}: {r.text[:300]}")
except Exception as e:
    print(f"  Error: {e}")

# ── 3. GET MCP endpoint (harus SSE response dulu untuk Streamable HTTP) ───────
sep("3. GET /gradio_api/mcp/ (SSE init)")
try:
    r = requests.get(
        f"{BASE}/gradio_api/mcp/",
        headers={"Accept": "text/event-stream"},
        timeout=15, stream=True
    )
    print(f"  HTTP {r.status_code}")
    print(f"  Content-Type: {r.headers.get('Content-Type')}")
    lines = []
    for line in r.iter_lines(decode_unicode=True):
        if line:
            lines.append(line)
            print(f"  > {line[:200]}")
        if len(lines) >= 10:
            break
except Exception as e:
    print(f"  Error: {e}")

# ── 4. POST ke MCP dengan Accept: application/json,text/event-stream ──────────
sep("4. POST /gradio_api/mcp/ (initialize, Accept both)")
try:
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    r = requests.post(
        f"{BASE}/gradio_api/mcp/",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        },
        timeout=20, stream=True
    )
    print(f"  HTTP {r.status_code}")
    print(f"  Content-Type: {r.headers.get('Content-Type')}")
    raw = r.content
    print(f"  body bytes ({len(raw)}): {raw[:500]}")
    if raw.strip():
        try:
            print(f"  JSON: {json.loads(raw.decode())}")
        except:
            # Mungkin SSE format
            for line in raw.decode(errors="replace").splitlines():
                if line.strip():
                    print(f"  line: {line[:200]}")
    else:
        print("  [empty body]")
except Exception as e:
    print(f"  Error: {e}")

# ── 5. Coba /run/predict (Gradio 3.x compat) ─────────────────────────────────
sep("5. POST /run/predict")
try:
    r = requests.post(
        f"{BASE}/run/predict",
        json={"fn_index": 0, "data": ["Hello, describe yourself in one sentence.", None, "text"]},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"  HTTP {r.status_code}: {r.text[:400]}")
except Exception as e:
    print(f"  Error: {e}")

print("\n[Done]")
