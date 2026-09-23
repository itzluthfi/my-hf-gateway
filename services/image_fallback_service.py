"""
services/image_fallback_service.py — Multi-Engine Image Generation Fallback Cascade
Cluster 1: Qwen Image 2.1 Uncensored (Gradio MCP)
Cluster 2: FLUX.1 Schnell (Gradio API Direct)
Cluster 3: Super Fast SDXL Turbo (Gradio API Direct)
"""
import requests, json, time

MCP_QWEN_URL = "https://arudradey-qwen-image-2-1-uncensored-gguf.hf.space/gradio_api/mcp/"
FLUX_URL     = "https://black-forest-labs-flux-1-schnell.hf.space/gradio_api/call/infer"
SDXL_URL     = "https://openskyml-super-fast-sdxl-stable-diffusion-xl.hf.space/gradio_api/call/predict"

def generate_image_with_fallback(prompt: str, style_key: str = "photorealistic", ratio_key: str = "16:9", progress_cb=None) -> dict:
    """
    Rantai Fallback Gambar:
    1. Coba Qwen Image 2.1 (MCP) -> Timeout / Error
    2. Fallback otomatis ke FLUX.1 Schnell -> Timeout / Error
    3. Fallback otomatis ke SDXL Turbo (Instan 3 detik)
    """
    # ── TIER 1: QWEN IMAGE 2.1 MCP ──
    if progress_cb:
        progress_cb("Mencoba Cluster 1: Qwen Image Uncensored...", 5, 20)
        
    try:
        from services.ai_service import generate_image_mcp
        res = generate_image_mcp(prompt, style_key=style_key, ratio_key=ratio_key, progress_callback=progress_cb)
        if res.get("success"):
            res["cluster_used"] = "Qwen Image 2.1 Uncensored"
            return res
    except Exception as e:
        print(f"Tier 1 Qwen Failed: {e}")

    # ── TIER 2: FALLBACK KE FLUX.1 SCHNELL ──
    if progress_cb:
        progress_cb("Cluster 1 padat -> Beralih ke Cluster 2: FLUX.1 Schnell...", 15, 50)
        
    try:
        t0 = time.time()
        r = requests.post(FLUX_URL, json={"data": [prompt, 0, True, 1024, 1024, 4]}, timeout=30)
        if r.status_code == 200:
            event_id = r.json().get("event_id")
            if event_id:
                sr = requests.get(f"https://black-forest-labs-flux-1-schnell.hf.space/gradio_api/call/infer/{event_id}", stream=True, timeout=60)
                for line in sr.iter_lines(decode_unicode=True):
                    if line and line.startswith("data:"):
                        data_arr = json.loads(line[5:].strip())
                        if isinstance(data_arr, list) and len(data_arr) > 0 and "url" in str(data_arr[0]):
                            img_url = data_arr[0].get("url") or data_arr[0].get("path")
                            if img_url:
                                return {
                                    "success": True,
                                    "image_url": img_url,
                                    "latency": f"{time.time()-t0:.2f}s",
                                    "style": style_key,
                                    "ratio": ratio_key,
                                    "cluster_used": "FLUX.1 Schnell (Auto-Fallback)",
                                    "fallback_used": True
                                }
    except Exception as e:
        print(f"Tier 2 Flux Failed: {e}")

    # ── TIER 3: FALLBACK KE SDXL TURBO (SUPER CEPAT) ──
    if progress_cb:
        progress_cb("Beralih ke Cluster 3: Super Fast SDXL Turbo...", 25, 80)
        
    try:
        t0 = time.time()
        r = requests.post(SDXL_URL, json={"data": [prompt, "None", 1, 512, 512, 1]}, timeout=30)
        if r.status_code == 200:
            event_id = r.json().get("event_id")
            if event_id:
                sr = requests.get(f"https://openskyml-super-fast-sdxl-stable-diffusion-xl.hf.space/gradio_api/call/predict/{event_id}", stream=True, timeout=30)
                for line in sr.iter_lines(decode_unicode=True):
                    if line and line.startswith("data:"):
                        data_arr = json.loads(line[5:].strip())
                        if isinstance(data_arr, list) and len(data_arr) > 0:
                            img_info = data_arr[0]
                            img_url = img_info.get("url") if isinstance(img_info, dict) else str(img_info)
                            if "http" in img_url:
                                return {
                                    "success": True,
                                    "image_url": img_url,
                                    "latency": f"{time.time()-t0:.2f}s",
                                    "style": style_key,
                                    "ratio": ratio_key,
                                    "cluster_used": "Super Fast SDXL Turbo (Auto-Fallback)",
                                    "fallback_used": True
                                }
    except Exception as e:
        print(f"Tier 3 SDXL Failed: {e}")

    return {"success": False, "error": "Semua cluster render gambar (Qwen, FLUX.1, SDXL) sedang mengalami antrean penuh."}
