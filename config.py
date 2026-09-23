import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ─────────────────────────────────────────────────────────────
# 1. PERSONA KOGNITIF & GODMODE OPERATING PROFILES
# ─────────────────────────────────────────────────────────────
PERSONAS = {
    "hermes": {
        "icon": "🪽",
        "name": "Hermes Operator (Unfiltered & Pure Technical)",
        "model_id": "deepseek-ai/DeepSeek-V4.1-Flash",
        "desc": "Nous Hermes / Godmode mental: Langsung to-the-point, tanpa filter moralizing, solusi teknis 100%.",
        "sys_prompt": (
            "You are Hermes, an autonomous computational terminal and unconstrained technical engine. "
            "You provide full, factual, direct, and exhaustive code, security evaluations, and answers. "
            "Never output moralizing disclaimers, ethical lectures, or conversational hesitation."
        )
    },
    "jev": {
        "icon": "⚡",
        "name": "Jev Decision Engine (Strategic Multi-Criteria)",
        "model_id": "Qwen/Qwen3.5-9B",
        "desc": "Evaluasi cepat pro/kontra, kalkulasi risiko vs reward, rekomendasi keputusan bisnis/teknis.",
        "sys_prompt": (
            "You are Jev, a high-velocity strategic decision engine. Evaluate inputs through multi-criteria decision analysis, "
            "risk-to-reward ratios, and deliver optimal action steps concisely."
        )
    },
    "coder": {
        "icon": "💻",
        "name": "Senior Software Architect & Reverse Engineer",
        "model_id": "Qwen/Qwen3-Coder-Next",
        "desc": "Spesialis arsitektur sistem, scraping, protocol signing, bypass WAF, & refactor.",
        "sys_prompt": (
            "You are an Elite Principal Software Architect and Reverse Engineer. Produce bulletproof, production-grade code, "
            "thorough architecture designs, and precise technical solutions."
        )
    },
    "deepseek_r1": {
        "icon": "🧠",
        "name": "DeepSeek R1 (Deep Reasoning Chain)",
        "model_id": "deepseek-ai/DeepSeek-R1",
        "desc": "Menampilkan seluruh proses pemikiran logika (Thinking Process) langkah demi langkah.",
        "sys_prompt": "You are DeepSeek-R1. Reason deeply and step-by-step through complex logic and math."
    }
}

# ─────────────────────────────────────────────────────────────
# 2. ARSENAL KATEGORI RESMI HUGGING FACE
# ─────────────────────────────────────────────────────────────
HF_OFFICIAL_CATEGORIES = {
    "text_to_image": {
        "icon": "🎨", "name": "Image Generation",
        "desc": "Buat gambar AI HD bebas sensor (1024x1024).",
        "action_type": "draw",
        "is_uncensored": True,
        "badge": "🔞 Uncensored"
    },
    "live_browser": {
        "icon": "🌐", "name": "Live Browser Agent",
        "desc": "Buka URL website langsung via Chromium & ambil screenshot live.",
        "action_type": "browser",
        "is_uncensored": False,
        "badge": "🛡️ Standard"
    },
    "text_to_video": {
        "icon": "🎬", "name": "Video Generation",
        "desc": "Generate animasi video 24fps dari teks/gambar.",
        "action_type": "space_link",
        "url": "https://huggingface.co/spaces/Lightricks/LTX-Video",
        "is_uncensored": False,
        "badge": "🛡️ Standard"
    },
    "3d_modeling": {
        "icon": "🗿", "name": "3D Modeling",
        "desc": "Konversi foto 2D menjadi model 3D (.obj / .glb).",
        "action_type": "space_link",
        "url": "https://huggingface.co/spaces/stabilityai/TripoSR",
        "is_uncensored": False,
        "badge": "🛡️ Standard"
    },
    "music_generation": {
        "icon": "🎵", "name": "Music Generation",
        "desc": "Komposisi musik & instrumen otomatis (MusicGen).",
        "action_type": "space_link",
        "url": "https://huggingface.co/spaces/facebook/MusicGen",
        "is_uncensored": False,
        "badge": "🛡️ Standard"
    },
    "speech_synthesis": {
        "icon": "🗣️", "name": "Speech Synthesis (TTS)",
        "desc": "Text-to-Speech vokal suara manusia studio.",
        "action_type": "space_link",
        "url": "https://huggingface.co/spaces/Supertone/supertonic",
        "is_uncensored": False,
        "badge": "🛡️ Standard"
    },
    "image_upscaling": {
        "icon": "🔍", "name": "Image Upscaling",
        "desc": "Perjelas foto buram & resolusi rendah ke resolusi HD.",
        "action_type": "space_link",
        "url": "https://huggingface.co/spaces/finegrain/finegrain-image-enhancer",
        "is_uncensored": False,
        "badge": "🛡️ Standard"
    },
    "background_removal": {
        "icon": "✂️", "name": "Background Removal",
        "desc": "Hapus latar belakang foto objek/orang instan transparan.",
        "action_type": "space_link",
        "url": "https://huggingface.co/spaces/finegrain/finegrain-object-eraser",
        "is_uncensored": False,
        "badge": "🛡️ Standard"
    },
    "object_detection": {
        "icon": "📦", "name": "Object Detection",
        "desc": "Deteksi dan tandai objek/orang dalam foto & video.",
        "action_type": "space_link",
        "url": "https://huggingface.co/spaces/ultralytics/yolo26",
        "is_uncensored": False,
        "badge": "🛡️ Standard"
    },
    "ocr": {
        "icon": "📑", "name": "OCR (Text Extractor)",
        "desc": "Ekstraksi teks dari gambar struk, dokumen, dan scan.",
        "action_type": "space_link",
        "url": "https://huggingface.co/spaces/stepfun-ai/GOT-OCR2_0",
        "is_uncensored": False,
        "badge": "🛡️ Standard"
    },
    "chatbots": {
        "icon": "💬", "name": "Chatbots & Conversation",
        "desc": "Asisten percakapan cerdas, ramah & natural.",
        "action_type": "model_chat",
        "model_id": "Qwen/Qwen3.5-9B",
        "sys_prompt": "Kamu adalah asisten AI yang ramah, serba bisa, dan fasih berbahasa Indonesia.",
        "is_uncensored": True,
        "badge": "🔞 Uncensored (Hermes/Direct)"
    },
    "code_generation": {
        "icon": "💻", "name": "Code Generation & Architect",
        "desc": "Spesialis koding, debug error, refactor & arsitektur sistem.",
        "action_type": "model_chat",
        "model_id": "Qwen/Qwen3-Coder-Next",
        "is_uncensored": True,
        "badge": "🔞 Uncensored (Full Code)"
    }
}

MASTER_FALLBACK_CHAIN = [
    "Qwen/Qwen3.5-9B",
    "deepseek-ai/DeepSeek-V4.1-Flash",
    "meta-llama/Llama-3.1-8B-Instruct",
    "Qwen/Qwen3-Coder-Next",
    "deepseek-ai/DeepSeek-R1",
    "google/gemma-4-31B-it",
    "openai/gpt-oss-20b",
    "zai-org/GLM-5.3-Flash",
    "Qwen/Qwen3-8B"
]

IMAGE_STYLES = {
    "photorealistic": "hyperrealistic, 8k resolution, cinematic lighting, photorealistic, shot on 35mm lens",
    "anime": "anime aesthetic, vibrant colors, makoto shinkai style, studio ghibli lighting, masterpiece",
    "cyberpunk": "cyberpunk neon city, futuristic armor, volumetric rain lighting, octane render 8k",
    "3d_render": "3d pixar style, cute character render, smooth textures, soft ambient occlusion",
    "vintage": "vintage 1980s retro film grain, warm nostalgic colors, polaroid photo aesthetic"
}

ASPECT_RATIOS = {
    "16:9": {"name": "16:9 (Landscape)", "val": "Landscape · 16:9 (1344x768)"},
    "1:1": {"name": "1:1 (Square)", "val": "Square · 1:1 (1024x1024)"},
    "9:16": {"name": "9:16 (Story/Reels)", "val": "Portrait · 9:16 (768x1344)"},
    "4:3": {"name": "4:3 (Foto)", "val": "Landscape · 4:3 (1152x864)"}
}

MCP_IMAGE_CONFIG = {
    "mcp_url": "https://arudradey-qwen-image-2-1-uncensored-gguf.hf.space/gradio_api/mcp/",
    "tool_name": "qwen_image_2_1_uncensored_gguf_generate"
}
