"""
fetch_viral_spaces.py — Mengambil daftar Space Hugging Face paling viral, trending, & banyak di-like
"""
import sys, io, requests, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

print("=================================================================")
print(" Mengambil Data Space AI Trending & Viral di Hugging Face")
print("=================================================================\n")

# 1. Trending Spaces
try:
    r = requests.get("https://huggingface.co/api/trending?type=space&limit=30", timeout=10)
    if r.status_code == 200:
        items = r.json().get("recentlyTrending", [])
        print(f"[*] Menemukan {len(items)} Trending Spaces:")
        for item in items[:15]:
            space_id = item.get("repoData", {}).get("id") or item.get("id")
            likes = item.get("repoData", {}).get("likes", 0)
            print(f"  🔥 https://huggingface.co/spaces/{space_id} (Likes: {likes})")
except Exception as e:
    print(f"Error fetching trending: {e}")

# 2. Most Liked Spaces per Category
categories = ["image-to-image", "text-to-image", "text-generation", "text-to-speech", "image-segmentation"]
print("\n=================================================================")
print(" Space Paling Populer (Most Liked) per Kategori")
print("=================================================================\n")

for cat in categories:
    try:
        url = f"https://huggingface.co/api/spaces?sort=likes&direction=-1&limit=5&filter={cat}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            spaces = r.json()
            print(f"📁 Kategori: {cat.upper()}")
            for s in spaces:
                sid = s.get("id")
                likes = s.get("likes", 0)
                sdk = s.get("sdk", "gradio")
                print(f"   • {sid} (❤️ {likes} likes | SDK: {sdk})")
            print()
    except Exception as e:
        print(f"Error {cat}: {e}")
