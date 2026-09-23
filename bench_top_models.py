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

top_models = [
    ("DeepSeek-R1 (Top Reasoning)", "deepseek-ai/DeepSeek-R1"),
    ("Llama-3.1-8B-Instruct (Paling Cepat & Seimbang)", "meta-llama/Llama-3.1-8B-Instruct"),
    ("Qwen-3.5-9B (Top Multilingual & Coding)", "Qwen/Qwen3.5-9B"),
]

prompt = "Buatkan fungsi Python 1 baris untuk membalikkan kalimat kata per kata."

print("=================================================================")
print(" Uji Performa Model-Model Terbaik di Hugging Face")
print("=================================================================\n")

for label, model_id in top_models:
    print(f"[*] Menguji: {label} [{model_id}]")
    t0 = time.time()
    try:
        r = requests.post(URL, json={
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.6
        }, headers=HEADERS, timeout=30)
        elapsed = time.time() - t0
        print(f"    Status: HTTP {r.status_code} ({elapsed:.2f}s)")
        if r.status_code == 200:
            res = r.json()
            choice = res.get("choices", [{}])[0].get("message", {})
            reply = choice.get("content") or choice.get("reasoning_content") or str(choice)
            print(f"    [HASIL]:\n    {reply.strip()[:250]}...")
        else:
            print(f"    [RESPONSE]: {r.text[:200]}")
    except Exception as e:
        print(f"    [ERROR]: {e}")
    print("-" * 65)
