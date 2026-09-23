"""
services/analytics_service.py — Token, Model Usage, User Stats, and Leaderboard Tracker
"""
import os
import json
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
STATS_FILE = os.path.join(DATA_DIR, "usage_analytics.json")
os.makedirs(DATA_DIR, exist_ok=True)


def _load_stats() -> dict:
    default_stats = {
        "total_requests": 0,
        "total_tokens_est": 0,
        "models_usage": {},      # { "model_id": { "calls": int, "tokens_est": int, "fallbacks": int } }
        "users_activity": {},    # { "user_id": { "name": str, "username": str, "calls": int, "last_seen": str } }
        "action_breakdown": {
            "chat": 0,
            "draw": 0,
            "edit_img": 0,
            "browser": 0
        },
        "start_time": time.time()
    }
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Pastikan key default ada
                for k, v in default_stats.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            return default_stats
    return default_stats


def _save_stats(data: dict):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving analytics: {e}")


def track_usage(user_id: int, user_name: str, username: str, action: str, model_id: str = None, prompt_tokens: int = 0, completion_tokens: int = 0, is_fallback: bool = False):
    """Mencatat aktivitas, estimasi token, model yang digunakan, dan user stats."""
    stats = _load_stats()
    
    # 1. Global counts
    stats["total_requests"] += 1
    total_tok = prompt_tokens + completion_tokens
    stats["total_tokens_est"] += total_tok

    # 2. Action breakdown
    if action in stats["action_breakdown"]:
        stats["action_breakdown"][action] += 1
    else:
        stats["action_breakdown"][action] = 1

    # 3. Model usage & ranking
    if model_id:
        if model_id not in stats["models_usage"]:
            stats["models_usage"][model_id] = {
                "calls": 0,
                "tokens_est": 0,
                "fallbacks": 0
            }
        stats["models_usage"][model_id]["calls"] += 1
        stats["models_usage"][model_id]["tokens_est"] += total_tok
        if is_fallback:
            stats["models_usage"][model_id]["fallbacks"] += 1

    # 4. User stats & Leaderboard
    uid_str = str(user_id)
    if uid_str not in stats["users_activity"]:
        stats["users_activity"][uid_str] = {
            "name": user_name,
            "username": username or "-",
            "calls": 0,
            "last_seen": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    stats["users_activity"][uid_str]["calls"] += 1
    stats["users_activity"][uid_str]["name"] = user_name
    stats["users_activity"][uid_str]["username"] = username or "-"
    stats["users_activity"][uid_str]["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S")

    _save_stats(stats)


def get_analytics_summary() -> dict:
    """Mengambil rangkuman statistik untuk Admin Dashboard."""
    stats = _load_stats()
    
    # Rank models by calls
    sorted_models = sorted(
        stats["models_usage"].items(), 
        key=lambda x: x[1]["calls"], 
        reverse=True
    )
    
    # Rank active users by calls
    sorted_users = sorted(
        stats["users_activity"].items(), 
        key=lambda x: x[1]["calls"], 
        reverse=True
    )
    
    uptime_sec = int(time.time() - stats.get("start_time", time.time()))
    hours = uptime_sec // 3600
    minutes = (uptime_sec % 3600) // 60

    return {
        "uptime": f"{hours}h {minutes}m",
        "total_requests": stats["total_requests"],
        "total_tokens_est": stats["total_tokens_est"],
        "action_breakdown": stats["action_breakdown"],
        "top_models": sorted_models[:8],
        "top_users": sorted_users[:8],
        "unique_users_count": len(stats["users_activity"])
    }
