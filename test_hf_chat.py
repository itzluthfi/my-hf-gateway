import sys, io, requests, time, os
from dotenv import load_dotenv

load_dotenv()
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HF_TOKEN = os.getenv("HF_TOKEN", "")
URL = "https://router.huggingface.co/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

test_models = [
    "deepseek-ai/DeepSeek-V4.1-Flash",
    "Qwen/Qwen3-8B",
    "meta-llama/Llama-3.1-8B-Instruct",
    "zai-org/GLM-5.3-Flash",
    "prism-ml/Ternary-Bonsai-27B-gguf"
]

prompt = "Halo! Siapa kamu dan apa kelebihanmu? Jawab singkat saja dalam 1-2 kalimat bahasa Indonesia."

print("=================================================================")
print(" Menguji Hugging Face Router (OpenAI-Compatible API)")
print("=================================================================\n")

for m in test_models:
    print(f"[*] Testing Model: {m}")
    payload = {
        "model": m,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 120,
        "temperature": 0.7
    }
    t0 = time.time()
    try:
        r = requests.post(URL, json=payload, headers=HEADERS, timeout=30)
        elapsed = time.time() - t0
        print(f"    Status: HTTP {r.status_code} ({elapsed:.2f}s)")
        if r.status_code == 200:
            data = r.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"    [SUKSES] Jawaban:\n    {reply.strip()}")
        else:
            print(f"    [GAGAL] Response: {r.text[:250]}")
    except Exception as e:
        print(f"    [ERROR] {e}")
    print("-" * 65)
