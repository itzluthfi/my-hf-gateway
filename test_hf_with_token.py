import sys, io, json, time, requests, os
from dotenv import load_dotenv

load_dotenv()
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HF_TOKEN = os.getenv("HF_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

# Daftar model yang diuji
models = [
    {"name": "Qwen 2.5 0.5B Instruct", "id": "Qwen/Qwen2.5-0.5B-Instruct"},
    {"name": "Qwen 2.5 1.5B Instruct", "id": "Qwen/Qwen2.5-1.5B-Instruct"},
    {"name": "SmolLM2 1.7B Instruct", "id": "HuggingFaceTB/SmolLM2-1.7B-Instruct"},
    {"name": "SmolLM2 360M Instruct", "id": "HuggingFaceTB/SmolLM2-360M-Instruct"},
    {"name": "Qwen 2.5 7B Instruct", "id": "Qwen/Qwen2.5-7B-Instruct"},
    {"name": "Dolphin 2.9.4 Gemma 2 2B (Uncensored)", "id": "cognitivecomputations/dolphin-2.9.4-gemma2-2b"},
    {"name": "Mistral 7B Instruct v0.3", "id": "mistralai/Mistral-7B-Instruct-v0.3"}
]

prompt = "Halo! Siapa kamu, apa kelebihan utamamu? Jawab singkat saja dalam 1-2 kalimat bahasa Indonesia."

print("=================================================================")
print(" Menguji Hugging Face Serverless Inference API dengan Token")
print("=================================================================\n")

# Endpoint format OpenAI compatibility yang didukung HF Router
for m in models:
    url = f"https://router.huggingface.co/hf-inference/models/{m['id']}/v1/chat/completions"
    payload = {
        "model": m["id"],
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    print(f"[*] Menguji: {m['name']}")
    print(f"    ID: {m['id']}")
    t0 = time.time()
    try:
        r = requests.post(url, json=payload, headers=HEADERS, timeout=25)
        elapsed = time.time() - t0
        print(f"    Status: HTTP {r.status_code} ({elapsed:.2f}s)")
        
        if r.status_code == 200:
            res = r.json()
            content = res.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"    [SUKSES] Jawaban:\n    {content.strip()}")
        else:
            # Coba legacy endpoint jika router v1 belum aktif untuk model tertentu
            legacy_url = f"https://api-inference.huggingface.co/models/{m['id']}"
            r2 = requests.post(legacy_url, json={"inputs": prompt, "parameters": {"max_new_tokens": 80}}, headers=HEADERS, timeout=20)
            if r2.status_code == 200:
                print(f"    [SUKSES via Legacy API] Jawaban:\n    {r2.text[:200]}")
            else:
                print(f"    [INFO] Response: {r.text[:250]}")
    except Exception as e:
        print(f"    [ERROR] {e}")
    print("-" * 65)
