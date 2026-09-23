"""
test_hf_inference.py — Tes koneksi gratis langsung ke Hugging Face Serverless Inference API
Menguji model ringan:
1. Qwen/Qwen2.5-0.5B-Instruct
2. Qwen/Qwen2.5-1.5B-Instruct
3. HuggingFaceTB/SmolLM2-1.7B-Instruct
4. cognitivecomputations/dolphin-2.9.4-gemma2-2b (Uncensored)
"""
import sys, io, json, time, requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Serverless Inference API (Router v1)
API_URL = "https://router.huggingface.co/hf-inference/models"

models = [
    {"name": "Qwen2.5-0.5B-Instruct", "id": "Qwen/Qwen2.5-0.5B-Instruct"},
    {"name": "Qwen2.5-1.5B-Instruct", "id": "Qwen/Qwen2.5-1.5B-Instruct"},
    {"name": "SmolLM2-1.7B-Instruct", "id": "HuggingFaceTB/SmolLM2-1.7B-Instruct"},
    {"name": "Dolphin-2.9.4-Gemma2-2B (Uncensored)", "id": "cognitivecomputations/dolphin-2.9.4-gemma2-2b"},
]

prompt = "Halo! Jelaskan secara singkat dalam 1 kalimat apa itu satelit antariksa."

print("=================================================================")
print(" Menguji Hugging Face Serverless Inference API (Gratis Publik)")
print("=================================================================\n")

for m in models:
    url = f"{API_URL}/{m['id']}/v1/chat/completions"
    payload = {
        "model": m["id"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 80,
        "temperature": 0.7
    }
    print(f"[*] Testing: {m['name']} ({m['id']})")
    t0 = time.time()
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
        elapsed = time.time() - t0
        print(f"    Status: HTTP {r.status_code} ({elapsed:.2f}s)")
        if r.status_code == 200:
            res = r.json()
            reply = res.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"    [SUKSES] Jawaban: {reply.strip()[:200]}")
        else:
            print(f"    [INFO] Response: {r.text[:250]}")
    except Exception as e:
        print(f"    [ERROR] {e}")
    print("-" * 65)
