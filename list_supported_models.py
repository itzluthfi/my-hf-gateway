import sys, io, requests, os
from dotenv import load_dotenv

load_dotenv()
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HF_TOKEN = os.getenv("HF_TOKEN", "")
url = "https://router.huggingface.co/v1/models"

r = requests.get(url, headers={"Authorization": f"Bearer {HF_TOKEN}"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    model_list = data.get("data", [])
    print(f"Total model aktif: {len(model_list)}")
    for m in model_list[:25]:
        print(f"• {m.get('id')}")
else:
    print(f"Response: {r.text}")
