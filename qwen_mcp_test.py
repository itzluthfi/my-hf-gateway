"""
qwen_mcp_test.py — Test connectivity and generate with Qwen Image 2.1 Uncensored MCP Server
"""

import json
import time
import sys
import requests

# Fix Windows console encoding
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://arudradey-qwen-image-2-1-uncensored-gguf.hf.space"
MCP_URL  = f"{BASE_URL}/gradio_api/mcp/"

SESSION_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


# ────────────────────────────────────────────────
# MCP helpers
# ────────────────────────────────────────────────

def mcp_initialize() -> dict | None:
    """Send MCP initialize handshake."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "qwen-mcp-client", "version": "1.0"},
        },
    }
    try:
        r = requests.post(MCP_URL, json=payload, headers=SESSION_HEADERS, timeout=20)
        print(f"[initialize] HTTP {r.status_code}")
        if r.status_code == 200:
            return r.json()
        print("  body:", r.text[:300])
        return None
    except Exception as e:
        print(f"[initialize] Error: {e}")
        return None


def mcp_list_tools(session_id: str = None) -> list:
    """List available MCP tools."""
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    hdrs = {**SESSION_HEADERS}
    if session_id:
        hdrs["Mcp-Session-Id"] = session_id
    try:
        r = requests.post(MCP_URL, json=payload, headers=hdrs, timeout=20)
        print(f"[tools/list] HTTP {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            tools = data.get("result", {}).get("tools", [])
            return tools
        print("  body:", r.text[:300])
        return []
    except Exception as e:
        print(f"[tools/list] Error: {e}")
        return []


def mcp_call_tool(tool_name: str, args: dict, session_id: str = None) -> dict | None:
    """Call an MCP tool by name."""
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": args,
        },
    }
    hdrs = {**SESSION_HEADERS}
    if session_id:
        hdrs["Mcp-Session-Id"] = session_id
    try:
        r = requests.post(MCP_URL, json=payload, headers=hdrs, timeout=120)
        print(f"[tools/call:{tool_name}] HTTP {r.status_code}")
        if r.status_code == 200:
            return r.json()
        print("  body:", r.text[:500])
        return None
    except Exception as e:
        print(f"[tools/call:{tool_name}] Error: {e}")
        return None


# ────────────────────────────────────────────────
# Gradio REST fallback (direct predict)
# ────────────────────────────────────────────────

def gradio_predict(prompt: str, mode: str = "text") -> dict | None:
    """
    Fallback: call Gradio /run/predict or /api/predict directly.
    Works even without full MCP session negotiation.
    """
    url = f"{BASE_URL}/gradio_api/call/generate"
    payload = {
        "data": [prompt, None, mode],
    }
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
        print(f"[gradio_predict] HTTP {r.status_code}")
        if r.status_code == 200:
            event_id = r.json().get("event_id")
            print(f"  event_id: {event_id}")
            if event_id:
                return gradio_poll_result(event_id)
            return r.json()
        print("  body:", r.text[:500])
        return None
    except Exception as e:
        print(f"[gradio_predict] Error: {e}")
        return None


def gradio_poll_result(event_id: str, timeout: int = 60) -> dict | None:
    """Poll SSE result stream for a Gradio event_id."""
    url = f"{BASE_URL}/gradio_api/call/generate/{event_id}"
    try:
        resp = requests.get(url, stream=True, timeout=timeout,
                            headers={"Accept": "text/event-stream"})
        print(f"[poll_result] HTTP {resp.status_code}")
        full = []
        for line in resp.iter_lines(decode_unicode=True):
            if line:
                print(f"  stream> {line[:200]}")
                full.append(line)
            if line.startswith("data:") and '"success"' in line:
                break
        return {"raw": full}
    except Exception as e:
        print(f"[poll_result] Error: {e}")
        return None


# ────────────────────────────────────────────────
# Main test sequence
# ────────────────────────────────────────────────

def main():
    print("=" * 58)
    print("  Qwen Image 2.1 Uncensored — MCP Connectivity Test")
    print("=" * 58)
    print(f"MCP URL: {MCP_URL}\n")

    # 1. MCP Initialize
    print("── Step 1: MCP Initialize ──────────────────────────────")
    init_resp = mcp_initialize()
    session_id = None
    if init_resp:
        session_id = (init_resp.get("result", {})
                                .get("sessionId") or
                      init_resp.get("id"))
        print(f"  Server info: {json.dumps(init_resp.get('result', {}), indent=2)[:400]}")
    else:
        print("  Initialize failed — will try direct Gradio calls.\n")

    # 2. List tools
    print("\n── Step 2: List MCP Tools ──────────────────────────────")
    tools = mcp_list_tools(session_id)
    if tools:
        for t in tools:
            print(f"  • {t.get('name')}: {t.get('description','')[:80]}")
    else:
        print("  Could not list tools via MCP.")

    # 3. Call update_ui_mode
    print("\n── Step 3: Call update_ui_mode (mode=text) ─────────────")
    ui_result = mcp_call_tool(
        "qwen_image_2_1_uncensored_gguf_update_ui_mode",
        {"mode": "text"},
        session_id,
    )
    if ui_result:
        print(f"  Result: {json.dumps(ui_result, indent=2)[:300]}")

    # 4. Generate — via MCP tool
    print("\n── Step 4: Generate (MCP tool) ─────────────────────────")
    prompt = "Describe the Milky Way galaxy in exactly 2 sentences."
    gen_result = mcp_call_tool(
        "qwen_image_2_1_uncensored_gguf_generate",
        {
            "message": prompt,
            "request": None,
            "mode": "text",
        },
        session_id,
    )
    if gen_result:
        print(f"  Result (truncated 600):\n{json.dumps(gen_result, indent=2)[:600]}")
    else:
        # 5. Fallback: Gradio predict
        print("\n── Step 5: Fallback — Gradio REST predict ───────────────")
        gradio_predict(prompt, mode="text")

    print("\n✓ Test complete.")


if __name__ == "__main__":
    main()
