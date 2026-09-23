import sys, io, requests, time, json, os
from dotenv import load_dotenv

load_dotenv()
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HF_TOKEN = os.getenv("HF_TOKEN", "")
ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}

# 1. LLM Chat Candidates (Multi-provider / Fallback)
llm_candidates = [
    ("Reasoning Master", "deepseek-ai/DeepSeek-R1"),
    ("High-Speed Chat", "deepseek-ai/DeepSeek-V4.1-Flash"),
    ("Indonesia & Code Master", "Qwen/Qwen3.5-9B"),
    ("General Stable", "meta-llama/Llama-3.1-8B-Instruct"),
    ("Ultra-Fast Micro", "Qwen/Qwen3-8B"),
]

print("=================================================================")
print(" 1. RISIET & BENCHMARK LLM ROUTER (Multi-Fallback)")
print("=================================================================\n")

for label, mid in llm_candidates:
    print(f"[*] Testing LLM: {label} -> {mid}")
    t0 = time.time()
    try:
        r = requests.post(ROUTER_URL, json={
            "model": mid,
            "messages": [{"role": "user", "content": "Hai! Jawab dalam 1 kata: 'Siap'."}],
            "max_tokens": 30
        }, headers=HEADERS, timeout=15)
        elapsed = time.time() - t0
        print(f"    Status: HTTP {r.status_code} ({elapsed:.2f}s)")
    except Exception as e:
        print(f"    Error: {e}")

# 2. Image Generation Spaces Candidates
print("\n=================================================================")
print(" 2. RISET MCP IMAGE GEN SPACES (Gratis & Active)")
print("=================================================================\n")

image_spaces = [
    ("Qwen Image 2.1 Uncensored", "https://arudradey-qwen-image-2-1-uncensored-gguf.hf.space/gradio_api/mcp/"),
    ("FLUX.1 Schnell (Fast & Free)", "https://black-forest-labs-flux-1-schnell.hf.space/gradio_api/info"),
    ("Stable Diffusion 3.5 Large", "https://stabilityai-stable-diffusion-3-5-large.hf.space/gradio_api/info")
]

for name, url in image_spaces:
    print(f"[*] Testing Space Endpoint: {name}")
    try:
        r = requests.get(url, timeout=10)
        print(f"    Status: HTTP {r.status_code} (Endpoint Accessible)")
    except Exception as e:
        print(f"    Error: {e}")

print("\n[Done Probe]")
