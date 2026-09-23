"""
qwen_mcp_client.py — Full interactive CLI for Qwen Image 2.1 Uncensored via MCP + Gradio REST

Usage:
  python qwen_mcp_client.py                        # interactive chat
  python qwen_mcp_client.py "your prompt here"     # single prompt, non-interactive
"""

import json
import sys
import time
import requests
from typing import Optional

BASE_URL = "https://arudradey-qwen-image-2-1-uncensored-gguf.hf.space"
MCP_URL  = f"{BASE_URL}/gradio_api/mcp/"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

_req_id = 0
_session_id: Optional[str] = None


def _next_id() -> int:
    global _req_id
    _req_id += 1
    return _req_id


# ───── MCP protocol helpers ─────

def _post(payload: dict) -> Optional[dict]:
    hdrs = {**HEADERS}
    if _session_id:
        hdrs["Mcp-Session-Id"] = _session_id
    try:
        r = requests.post(MCP_URL, json=payload, headers=hdrs, timeout=120)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def mcp_init() -> bool:
    global _session_id
    resp = _post({
        "jsonrpc": "2.0", "id": _next_id(),
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "qwen-mcp", "version": "1.0"},
        },
    })
    if resp and "result" in resp:
        _session_id = resp["result"].get("sessionId") or resp.get("id")
        return True
    return False


def mcp_generate(prompt: str, mode: str = "text") -> Optional[str]:
    resp = _post({
        "jsonrpc": "2.0", "id": _next_id(),
        "method": "tools/call",
        "params": {
            "name": "qwen_image_2_1_uncensored_gguf_generate",
            "arguments": {"message": prompt, "request": None, "mode": mode},
        },
    })
    if resp and "result" in resp:
        content = resp["result"].get("content", [])
        for item in content:
            if item.get("type") == "text":
                return item.get("text", "")
        return str(resp["result"])
    return None


# ───── Gradio REST fallback ─────

def gradio_generate(prompt: str) -> Optional[str]:
    """Post to /gradio_api/call/generate, poll SSE stream."""
    try:
        r = requests.post(
            f"{BASE_URL}/gradio_api/call/generate",
            json={"data": [prompt, None, "text"]},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if r.status_code != 200:
            return None
        event_id = r.json().get("event_id")
        if not event_id:
            return None

        # Poll SSE
        sr = requests.get(
            f"{BASE_URL}/gradio_api/call/generate/{event_id}",
            stream=True, timeout=90,
            headers={"Accept": "text/event-stream"},
        )
        result_text = []
        for line in sr.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data:"):
                raw = line[5:].strip()
                try:
                    data = json.loads(raw)
                    if isinstance(data, list) and data:
                        result_text.append(str(data[0]))
                except Exception:
                    result_text.append(raw)
        return "\n".join(result_text) if result_text else None
    except Exception as e:
        return f"[Error] {e}"


# ───── Main ─────

def ask(prompt: str) -> str:
    # Try MCP first
    ans = mcp_generate(prompt)
    if ans:
        return ans
    # Fallback to Gradio REST
    ans = gradio_generate(prompt)
    return ans or "[No response]"


def interactive():
    print("╔══════════════════════════════════════════════╗")
    print("║  Qwen Image 2.1 Uncensored — MCP CLI Client  ║")
    print("║  Type 'exit' or Ctrl+C to quit               ║")
    print("╚══════════════════════════════════════════════╝\n")

    # Init
    sys.stdout.write("Connecting to MCP server... ")
    sys.stdout.flush()
    ok = mcp_init()
    print("✓ Connected (MCP)" if ok else "⚠ MCP init failed, using Gradio REST fallback")
    print()

    while True:
        try:
            prompt = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit", "q"}:
            print("Bye!")
            break
        print("Thinking...", end="\r")
        t0 = time.time()
        answer = ask(prompt)
        elapsed = time.time() - t0
        print(f"{'Qwen':>4}: {answer}\n       [latency: {elapsed:.1f}s]\n")


def single(prompt: str):
    sys.stdout.write("Connecting... ")
    sys.stdout.flush()
    ok = mcp_init()
    print("✓" if ok else "⚠ MCP fallback")
    t0 = time.time()
    answer = ask(prompt)
    elapsed = time.time() - t0
    print(f"\nPrompt : {prompt}")
    print(f"Answer : {answer}")
    print(f"Latency: {elapsed:.1f}s")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        single(" ".join(sys.argv[1:]))
    else:
        interactive()
