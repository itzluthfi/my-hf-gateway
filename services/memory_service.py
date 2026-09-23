"""
services/memory_service.py — Persistent Memory & RAG Retrieval Engine
"""
import os, json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MEMORY_FILE = os.path.join(DATA_DIR, "chat_memory.json")
KNOWLEDGE_FILE = os.path.join(DATA_DIR, "knowledge_base.json")

os.makedirs(DATA_DIR, exist_ok=True)

def _load_json(file_path: str, default: dict) -> dict:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def _save_json(file_path: str, data: dict):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

# ── 1. Conversation History (Memory) ──
def get_user_history(user_id: int, max_turns: int = 6) -> list:
    """Mengambil riwayat percakapan terakhir user."""
    all_mem = _load_json(MEMORY_FILE, {})
    return all_mem.get(str(user_id), [])[-max_turns:]

def save_user_turn(user_id: int, role: str, content: str):
    """Menyimpan interaksi pesan user & bot."""
    all_mem = _load_json(MEMORY_FILE, {})
    uid_str = str(user_id)
    if uid_str not in all_mem:
        all_mem[uid_str] = []
    all_mem[uid_str].append({"role": role, "content": content})
    # Batasi riwayat maksimal 20 turn per user
    if len(all_mem[uid_str]) > 20:
        all_mem[uid_str] = all_mem[uid_str][-20:]
    _save_json(MEMORY_FILE, all_mem)

def clear_user_memory(user_id: int):
    """Mereset ingatan percakapan user."""
    all_mem = _load_json(MEMORY_FILE, {})
    all_mem.pop(str(user_id), None)
    _save_json(MEMORY_FILE, all_mem)

# ── 2. Local Knowledge Base & RAG Retriever ──
def retrieve_rag_context(query: str) -> str:
    """Mencari potongan informasi relevan dari knowledge base lokal."""
    kb = _load_json(KNOWLEDGE_FILE, {
        "workspace": "FREELANCE Automation Hub",
        "bot_info": "Hugging Face Gateway Bot Telegram terhubung ke 138+ model AI.",
        "features": "Image Generation (Qwen MCP), Video (LTX), 3D (TripoSR), Audio (MusicGen)."
    })
    
    matches = []
    q_words = query.lower().split()
    for k, v in kb.items():
        if any(w in k.lower() or w in str(v).lower() for w in q_words if len(w) > 3):
            matches.append(f"• {k}: {v}")
            
    return "\n".join(matches) if matches else ""
