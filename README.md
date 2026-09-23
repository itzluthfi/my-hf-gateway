# my-hf-gateway

A Telegram bot that acts as a unified gateway for free Hugging Face models, featuring multi-provider fallback, MCP image generation, and headless browser automation.

---

## Features

- **Text & Reasoning Router**: Uses Hugging Face Serverless Router (`https://router.huggingface.co/v1`) with fallback across multiple models (`Qwen/Qwen3.5-9B`, `deepseek-ai/DeepSeek-V4.1-Flash`, `meta-llama/Llama-3.1-8B-Instruct`, `deepseek-ai/DeepSeek-R1`, etc.).
- **Uncensored Image Generation**: Generates 1024x1024 images via Gradio MCP (`qwen_image_2_1_uncensored_gguf_generate`) with fallback to FLUX.1 and SDXL Turbo.
- **Image-to-Image Editing**: Send a photo as reference, then specify changes in text.
- **Live Browser Agent**: Uses Playwright Chromium to open web pages and send screenshots back to chat (`/browse <url>`).
- **Context Memory & RAG**: Multi-turn conversation memory with local knowledge base support.
- **Dual Interface**: Interactive inline keyboards and standard Telegram slash commands (`/start`, `/draw`, `/browse`, `/persona`, `/stop`, `/reset`, `/settings`, `/status`).

---

## Architecture

```
huggingface-gateway/
├── bot.py                        # Telegram bot runner (python-telegram-bot)
├── config.py                     # Model catalog, presets, and aspect ratios
├── services/
│   ├── ai_service.py             # LLM router and MCP image generator
│   ├── image_fallback_service.py # Multi-cluster image fallback engine
│   ├── browser_service.py        # Playwright headless browser capture
│   ├── memory_service.py         # Multi-turn memory & local RAG
│   └── telegram_setup.py         # Bot command menu registrar
├── data/                         # Local storage for chat memory and screenshots
├── Dockerfile                    # Container definition with Chromium dependencies
├── docker-compose.yml            # Deployment compose file
└── DEPLOYMENT_GUIDE.md           # Setup instructions for VPS hosting
```

---

## Prerequisites

- Python 3.10+
- Hugging Face Access Token (read access)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

---

## Quick Start (Local)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/itzluthfi/my-hf-gateway.git
   cd my-hf-gateway
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure environment:**
   Create a `.env` file based on `.env.example`:
   ```env
   HF_TOKEN=hf_your_token_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_ID=your_telegram_user_id
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

---

## Deployment (Docker)

```bash
docker compose up -d --build
```

View logs:
```bash
docker compose logs -f
```

---

## Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Open main interactive dashboard |
| `/menu` | Browse official Hugging Face categories |
| `/draw <prompt>` | Generate an image with active style and ratio |
| `/browse <url>` | Open a website live and receive a screenshot |
| `/persona` | Switch AI personality (Hermes, Jev, Coder, R1) |
| `/stop` | Cancel active generation or browsing task |
| `/reset` | Clear conversation memory |
| `/settings` | Configure visual style and canvas aspect ratio |
| `/status` | Check server and cluster health |

---

## License

MIT
