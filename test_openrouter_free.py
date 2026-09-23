"""
test_openrouter_free.py — Tes model ringan uncensored / open source via OpenRouter Free Tier
Endpoint: https://openrouter.ai/api/v1/chat/completions
"""
import sys, io, json, time, requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Endpoint OpenRouter
URL = "https://openrouter.ai/api/v1/chat/completions"

# Model-model gratis / uncensored populer di OpenRouter
free_models = [
    {"name": "CognitiveComputations: Dolphin 3.0 Mistral 24B (Free)", "id": "cognitivecomputations/dolphin3.0-mistral-24b:free"},
    {"name": "Qwen 2.5 7B Instruct (Free)", "id": "qwen/qwen-2.5-7b-instruct:free"},
    {"name": "Venice Uncensored (Free)", "id": "venice/uncensored:free"},
    {"name": "Meta: Llama 3.2 1B Instruct (Free)", "id": "meta-llama/llama-3.2-1b-instruct:free"},
    {"name": "Google: Gemma 2 9B (Free)", "id": "google/gemma-2-9b-it:free"}
]

prompt = "Siapa kamu dan apa kelebihan utamamu? Jawab dalam 1 kalimat bahasa Indonesia."

print("=================================================================")
print(" Menguji OpenRouter Free Tier Model (Uncensored / Open Models)")
print("=================================================================\n")

for m in free_models:
    payload = {
        "model": m["id"],
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100
    }
    print(f"[*] Testing: {m['name']}")
    t0 = time.time()
    try:
        r = requests.post(
            URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                # Tanpa auth key / anonymous check
            },
            timeout=15
        )
        elapsed = time.time() - t0
        print(f"    Status: HTTP {r.status_code} ({elapsed:.2f}s)")
        print(f"    Body: {r.text[:200]}")
    except Exception as e:
        print(f"    [ERROR] {e}")
    print("-" * 65)
