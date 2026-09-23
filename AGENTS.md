# AGENTS.md — Hugging Face Gateway Multi-AI Bot

## 🧠 System Architecture & Memory
- **Memory Layer**: In-memory user session state + JSON file-based persistent history per chat ID.
- **RAG Engine**: Simple local keyword/embedding retriever against workspace documentation and knowledge base.
- **Router Layer**: Hugging Face Serverless Router (`https://router.huggingface.co/v1`) with 9-layer auto-fallback.
- **MCP Tools**: Streamable HTTP Gradio MCP tools for image generation and multimodal processing.

## 🛠️ Operating Directives
- Respond directly, concisely, and helpfully to user prompts.
- Maintain persistent context across multiple turns using user session memory.
- Provide factual, structured, and production-ready technical outputs without unnecessary disclaimers.
