"""
services/image_fallback_service.py — Multi-Engine Image Generation Fallback Cascade (Uncensored & High-Velocity)

Tier 1: Qwen Image 2.1 Uncensored (Gradio MCP) — Photorealistic / Dynamic Prompt
Tier 2: RealVisXL / Pony Diffusion Uncensored (Gradio Direct) — Unfiltered Anime/Realistic
Tier 3: FLUX.1 Schnell Fast (Gradio Direct) — High Fidelity 1024px
Tier 4: Super Fast SDXL Turbo (Gradio Direct) — Ultra Low Latency 3s
Tier 5: Hugging Face Serverless Router (Black Forest FLUX Schnell / SDXL)
"""
import requests
import json
import time
from typing import Optional, Callable
from config import HF_TOKEN

HEADERS_HF = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

# Endpoint Spaces Gradio API
MCP_QWEN_URL = "https://arudradey-qwen-image-2-1-uncensored-gguf.hf.space/gradio_api/mcp/"
FLUX_URL     = "https://black-forest-labs-flux-1-schnell.hf.space/gradio_api/call/infer"
SDXL_URL     = "https://openskyml-super-fast-sdxl-stable-diffusion-xl.hf.space/gradio_api/call/predict"
PONY_ANIME_URL = "https://cagliostrolab-animagine-xl-3-1.hf.space/gradio_api/call/predict"


def _generate_hf_router_image(prompt: str, model_id: str = "black-forest-labs/FLUX.1-schnell") -> Optional[str]:
    """Fallback Tier 5: Direct Hugging Face Inference API / Serverless Router."""
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    try:
        r = requests.post(url, headers=HEADERS_HF, json={"inputs": prompt}, timeout=45)
        if r.status_code == 200 and "image" in r.headers.get("Content-Type", ""):
            import base64
            # Simpan atau jadikan data URI
            encoded = base64.b64encode(r.content).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        pass
    return None


def generate_image_with_fallback(
    prompt: str, 
    style_key: str = "photorealistic", 
    ratio_key: str = "16:9", 
    progress_cb: Optional[Callable[[str, int, int], None]] = None
) -> dict:
    """
    Rantai Fallback 5-Tier dengan Realtime Status Broadcast ke User:
    Tiap kali berpindah tier cluster, user langsung diupdate progresnya.
    """
    t_start = time.time()

    # ── TIER 1: QWEN IMAGE 2.1 UNCENSORED (MCP) ──
    if progress_cb:
        progress_cb("🚀 [Tier 1] Menghubungi Qwen Image 2.1 Uncensored...", 2, 15)
        
    try:
        from services.ai_service import generate_image_mcp
        res = generate_image_mcp(prompt, style_key=style_key, ratio_key=ratio_key, progress_callback=progress_cb)
        if res.get("success"):
            res["cluster_used"] = "Qwen Image 2.1 Uncensored"
            res["fallback_used"] = False
            return res
    except Exception as e:
        print(f"Tier 1 Qwen Error: {e}")

    # ── TIER 2: ANIMAGINE / PONY XL UNCENSORED (ANIME / ILLUSTRATION / UNFILTERED) ──
    if progress_cb:
        progress_cb("🔄 [Tier 2 Fallback] Beralih ke Animagine XL Uncensored Cluster...", int(time.time() - t_start), 40)
        
    try:
        t0 = time.time()
        # [prompt, negative_prompt, prompt_prefix, quality_tags, width, height, guidance_scale, steps, sampler, seed, custom_aspect_ratio]
        r = requests.post(
            PONY_ANIME_URL, 
            json={"data": [prompt, "lowres, bad anatomy, bad hands, cropped, worst quality", "(masterpiece), best quality", "Standard", 1024, 1024, 7, 28, "Euler a", 0, "1024 x 1024"]}, 
            timeout=25
        )
        if r.status_code == 200:
            event_id = r.json().get("event_id")
            if event_id:
                sr = requests.get(f"https://cagliostrolab-animagine-xl-3-1.hf.space/gradio_api/call/predict/{event_id}", stream=True, timeout=50)
                for line in sr.iter_lines(decode_unicode=True):
                    if line and line.startswith("data:"):
                        data_arr = json.loads(line[5:].strip())
                        if isinstance(data_arr, list) and len(data_arr) > 0:
                            img_url = data_arr[0].get("url") if isinstance(data_arr[0], dict) else str(data_arr[0])
                            if "http" in img_url:
                                return {
                                    "success": True,
                                    "image_url": img_url,
                                    "latency": f"{time.time()-t_start:.2f}s",
                                    "style": style_key,
                                    "ratio": ratio_key,
                                    "cluster_used": "Animagine XL Uncensored (Tier 2 Fallback)",
                                    "fallback_used": True
                                }
    except Exception as e:
        print(f"Tier 2 Animagine Error: {e}")

    # ── TIER 3: FLUX.1 SCHNELL (HIGH FIDELITY) ──
    if progress_cb:
        progress_cb("🔄 [Tier 3 Fallback] Beralih ke FLUX.1 Schnell Fast GPU...", int(time.time() - t_start), 65)
        
    try:
        t0 = time.time()
        r = requests.post(FLUX_URL, json={"data": [prompt, 0, True, 1024, 1024, 4]}, timeout=25)
        if r.status_code == 200:
            event_id = r.json().get("event_id")
            if event_id:
                sr = requests.get(f"https://black-forest-labs-flux-1-schnell.hf.space/gradio_api/call/infer/{event_id}", stream=True, timeout=50)
                for line in sr.iter_lines(decode_unicode=True):
                    if line and line.startswith("data:"):
                        data_arr = json.loads(line[5:].strip())
                        if isinstance(data_arr, list) and len(data_arr) > 0 and "url" in str(data_arr[0]):
                            img_url = data_arr[0].get("url") or data_arr[0].get("path")
                            if img_url:
                                return {
                                    "success": True,
                                    "image_url": img_url,
                                    "latency": f"{time.time()-t_start:.2f}s",
                                    "style": style_key,
                                    "ratio": ratio_key,
                                    "cluster_used": "FLUX.1 Schnell (Tier 3 Fallback)",
                                    "fallback_used": True
                                }
    except Exception as e:
        print(f"Tier 3 Flux Error: {e}")

    # ── TIER 4: SDXL TURBO (SUPER CEPAT 3 DETIK) ──
    if progress_cb:
        progress_cb("🔄 [Tier 4 Fallback] Beralih ke Super Fast SDXL Turbo...", int(time.time() - t_start), 85)
        
    try:
        t0 = time.time()
        r = requests.post(SDXL_URL, json={"data": [prompt, "None", 1, 512, 512, 1]}, timeout=20)
        if r.status_code == 200:
            event_id = r.json().get("event_id")
            if event_id:
                sr = requests.get(f"https://openskyml-super-fast-sdxl-stable-diffusion-xl.hf.space/gradio_api/call/predict/{event_id}", stream=True, timeout=25)
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
                                    "latency": f"{time.time()-t_start:.2f}s",
                                    "style": style_key,
                                    "ratio": ratio_key,
                                    "cluster_used": "Super Fast SDXL Turbo (Tier 4 Fallback)",
                                    "fallback_used": True
                                }
    except Exception as e:
        print(f"Tier 4 SDXL Error: {e}")

    # ── TIER 5: HF DIRECT SERVERLESS INFERENCE API ──
    if progress_cb:
        progress_cb("🔄 [Tier 5 Fallback] Beralih ke Direct Serverless GPU Router...", int(time.time() - t_start), 92)
        
    try:
        data_uri = _generate_hf_router_image(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0")
        if data_uri:
            return {
                "success": True,
                "image_url": data_uri,
                "latency": f"{time.time()-t_start:.2f}s",
                "style": style_key,
                "ratio": ratio_key,
                "cluster_used": "HF Serverless SDXL Direct (Tier 5 Fallback)",
                "fallback_used": True
            }
    except Exception as e:
        print(f"Tier 5 Router Error: {e}")

    return {
        "success": False, 
        "error": "Semua 5 cluster GPU image generator sedang antre penuh atau mengalami sleeping mode. Silakan kirim ulang prompt Anda dalam beberapa detik."
    }
