import sys, io, requests, os
from dotenv import load_dotenv

load_dotenv()
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HF_TOKEN = os.getenv("HF_TOKEN", "")
url = "https://router.huggingface.co/hf-inference/models/Qwen/Qwen2.5-7B-Instruct/v1/chat/completions"

r = requests.post(
    url,
    headers={"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"},
    json={
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [{"role": "user", "content": "Hello"}]
    }
)

print(f"Status: {r.status_code}")
print(f"Response: {r.text}")
