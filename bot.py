"""
bot.py — Telegram Bot AI Multi-Model v6.0 (Dual-Mode: Full Interactive Buttons + Slash Commands)
"""
import sys, io, logging, asyncio, os, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
from services.ai_service import ask_llm, generate_image_mcp, generate_progress_bar
from services.browser_service import browse_and_capture
from services.memory_service import clear_user_memory
from services.analytics_service import track_usage, get_analytics_summary
from services.telegram_setup import register_bot_commands
from config import (
    TELEGRAM_BOT_TOKEN, ADMIN_ID, HF_OFFICIAL_CATEGORIES, 
    PERSONAS, IMAGE_STYLES, ASPECT_RATIOS
)

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

user_states = {}
active_user_tasks = {}

def get_user_state(uid: int) -> dict:
    if uid not in user_states:
        user_states[uid] = {
            "category": "chatbots",
            "persona": "hermes",
            "model_id": PERSONAS["hermes"]["model_id"],
            "model_name": PERSONAS["hermes"]["name"],
            "image_style": "photorealistic",
            "image_ratio": "16:9",
            "waiting_for": None,
            "ref_photo_url": None
        }
    return user_states[uid]


# ─────────────────────────────────────────────────────────────
# 1. TOMBOL MENU LENGKAP & ALUR STEP-BY-STEP
# ─────────────────────────────────────────────────────────────
def main_dashboard_keyboard(uid: int):
    st = get_user_state(uid)
    p_info = PERSONAS.get(st["persona"], PERSONAS["hermes"])
    
    rows = [
        [
            InlineKeyboardButton(f"🎭 Persona: {p_info['icon']} {p_info['name'].split()[0]}", callback_data="nav_personas"),
            InlineKeyboardButton("🌐 Live Browser", callback_data="action_browser_flow")
        ],
        [
            InlineKeyboardButton("🎨 Bikin Gambar", callback_data="action_draw_flow"),
            InlineKeyboardButton("🖼️ Edit Foto / Ref", callback_data="action_edit_img")
        ],
        [
            InlineKeyboardButton("📂 28 Kategori Resmi HF", callback_data="nav_categories")
        ],
        [
            InlineKeyboardButton("⚙️ Setting Studio", callback_data="nav_settings"),
            InlineKeyboardButton("🧹 Reset Ingatan", callback_data="btn_reset_memory"),
            InlineKeyboardButton("⚡ Status", callback_data="nav_status")
        ]
    ]
    
    # Tombol Khusus Admin jika UID cocok dengan ADMIN_ID
    if uid == ADMIN_ID and ADMIN_ID != 0:
        rows.append([
            InlineKeyboardButton("👑 Dasbor Admin & Usage Analytics", callback_data="nav_admin_panel")
        ])
        
    return InlineKeyboardMarkup(rows)


def cancel_button_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛑 Batalkan Proses", callback_data="btn_stop_process")]
    ])


def personas_keyboard(uid: int):
    st = get_user_state(uid)
    buttons = []
    for p_key, p in PERSONAS.items():
        is_act = "✅ " if st["persona"] == p_key else ""
        buttons.append([InlineKeyboardButton(f"{is_act}{p['icon']} {p['name']}", callback_data=f"set_persona:{p_key}")])
    buttons.append([InlineKeyboardButton("🔙 Menu Utama", callback_data="nav_main")])
    return InlineKeyboardMarkup(buttons)


def all_categories_keyboard(filter_type: str = "all"):
    buttons = [
        [
            InlineKeyboardButton("✨ Semua", callback_data="filter_cat:all"),
            InlineKeyboardButton("🔞 Uncensored Mode", callback_data="filter_cat:uncensored"),
            InlineKeyboardButton("🛡️ Standard Mode", callback_data="filter_cat:standard")
        ]
    ]
    
    items = []
    for k, v in HF_OFFICIAL_CATEGORIES.items():
        if filter_type == "uncensored" and not v.get("is_uncensored", False):
            continue
        if filter_type == "standard" and v.get("is_uncensored", False):
            continue
        items.append((k, v))

    for i in range(0, len(items), 2):
        row = []
        k1, v1 = items[i]
        badge = "🔞 " if v1.get("is_uncensored") else ""
        row.append(InlineKeyboardButton(f"{badge}{v1['icon']} {v1['name']}", callback_data=f"select_cat:{k1}"))
        if i + 1 < len(items):
            k2, v2 = items[i+1]
            badge2 = "🔞 " if v2.get("is_uncensored") else ""
            row.append(InlineKeyboardButton(f"{badge2}{v2['icon']} {v2['name']}", callback_data=f"select_cat:{k2}"))
        buttons.append(row)

    buttons.append([InlineKeyboardButton("🔙 Menu Utama", callback_data="nav_main")])
    return InlineKeyboardMarkup(buttons)


def settings_keyboard(uid: int):
    st = get_user_state(uid)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🎭 Gaya: {st['image_style'].replace('_',' ').title()}", callback_data="choose_style"),
            InlineKeyboardButton(f"📐 Rasio: {st['image_ratio']}", callback_data="choose_ratio")
        ],
        [
            InlineKeyboardButton("🔙 Menu Utama", callback_data="nav_main")
        ]
    ])


def after_generate_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎨 Generate Lagi", callback_data="action_draw_flow"),
            InlineKeyboardButton("🖼️ Edit Hasil Ini", callback_data="action_edit_img")
        ],
        [
            InlineKeyboardButton("🔙 Menu Utama", callback_data="nav_main")
        ]
    ])


def after_browser_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌐 Buka Web Lain", callback_data="action_browser_flow"),
            InlineKeyboardButton("🔙 Menu Utama", callback_data="nav_main")
        ]
    ])


# ─────────────────────────────────────────────────────────────
# 2. REALTIME PROGRESS ANIMATOR
# ─────────────────────────────────────────────────────────────
async def animate_progress_bar(msg, ratio_label: str, uid: int):
    steps = [(10, 2), (25, 4), (40, 7), (60, 11), (75, 14), (85, 16), (95, 17)]
    for percent, elapsed in steps:
        await asyncio.sleep(2)
        bar = generate_progress_bar(percent, total_blocks=10)
        text = f"🎨 Generating *{ratio_label}* · *{percent}%*\n`{bar}`\n⏱️ {elapsed}s"
        try:
            await msg.edit_text(text, reply_markup=cancel_button_keyboard(), parse_mode="Markdown")
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# 3. CORE EXECUTORS & TASK MANAGEMENT
# ─────────────────────────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    st = get_user_state(uid)
    # Reset pending states saat user menekan start/menu
    st["waiting_for"] = None
    p_info = PERSONAS.get(st["persona"], PERSONAS["hermes"])

    text = (
        f"👑 *HUGGING FACE MULTI-AI HUB v6.1*\n"
        f"Halo, *{user.first_name}*!\n\n"
        f"🪽 *Persona Aktif:* `{p_info['icon']} {p_info['name']}`\n"
        f"🎨 *Preset Gambar:* `{st['image_style'].title()}` ({st['image_ratio']})\n\n"
        "Pilih salah satu tombol fitur di bawah untuk memulai:"
    )
    await update.message.reply_text(text, reply_markup=main_dashboard_keyboard(uid), parse_mode="Markdown")


async def notify_admin_activity(context: ContextTypes.DEFAULT_TYPE, user, action_type: str, detail: str):
    """Kirim notifikasi aktivitas prompt/generate user ke Admin."""
    if not ADMIN_ID:
        return
    try:
        username = f"@{user.username}" if user.username else user.first_name
        text = (
            f"🔔 *[AKTIVITAS USER]*\n"
            f"👤 *User:* {user.first_name} (`{username}`) [ID: `{user.id}`]\n"
            f"⚡ *Aksi:* `{action_type}`\n"
            f"📝 *Prompt/Input:*\n_{detail}_\n"
            f"⏱️ *Waktu:* `{time.strftime('%Y-%m-%d %H:%M:%S')}`"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")
    except Exception as e:
        logging.warning(f"Gagal mengirim notif ke admin: {e}")


async def execute_browser_task(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_url: str):
    """Eksekusi Live Browser dengan Antrean dan tombol Stop."""
    uid = update.effective_user.id
    user = update.effective_user
    
    # Kirim notif ke admin
    await notify_admin_activity(context, user, "Live Browser", raw_url)

    status_msg = await update.message.reply_text(
        f"🌐 *Mempersiapkan browser ke:* `{raw_url}`...",
        reply_markup=cancel_button_keyboard(),
        parse_mode="Markdown"
    )

    async def _queue_cb(wait_pos: int, est_sec: int):
        await status_msg.edit_text(
            f"⏳ *Antrean Browser #{wait_pos}*\nServer sedang memproses tugas lain. Estimasi giliran: ~{est_sec}s...",
            reply_markup=cancel_button_keyboard(),
            parse_mode="Markdown"
        )

    async def _core_job():
        await status_msg.edit_text(
            f"🌐 *Membuka headless Chromium ke:* `{raw_url}`...",
            reply_markup=cancel_button_keyboard(),
            parse_mode="Markdown"
        )
        res = await browse_and_capture(raw_url)
        if res["success"]:
            caption = (
                f"🌐 *Live Web Capture:* `{res['title']}`\n"
                f"🔗 *URL:* {res['url']} (Status: `{res['status_code']}`)\n"
                f"⚡ *Engine:* `Headless Chromium (Playwright)` ({res['latency']})\n\n"
                f"📝 *Text Snippet:*\n_{res['text_snippet'][:300]}..._"
            )
            await update.message.reply_photo(
                photo=open(res["screenshot_path"], "rb"),
                caption=caption,
                reply_markup=after_browser_keyboard(),
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text(f"❌ Gagal membuka website: {res['error']}", reply_markup=after_browser_keyboard())

    async def _runner():
        from services.queue_service import run_in_queue
        await run_in_queue(_queue_cb, _core_job, estimated_job_seconds=15)

    task = asyncio.create_task(_runner())
    active_user_tasks[uid] = task
    try:
        await task
    except asyncio.CancelledError:
        try:
            await status_msg.edit_text("🛑 *Navigasi browser dibatalkan.*", reply_markup=after_browser_keyboard(), parse_mode="Markdown")
        except Exception:
            pass
    finally:
        active_user_tasks.pop(uid, None)


async def execute_image_generation(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str, ref_url: str = None):
    """Eksekusi Render Gambar dengan Antrean (Queue), Realtime Progress, dan Notif Admin."""
    uid = update.effective_user.id
    user = update.effective_user
    st = get_user_state(uid)
    ratio = st["image_ratio"]
    loop = asyncio.get_running_loop()

    # Kirim notif prompt generate ke admin
    act_name = "Edit Foto / Img2Img" if ref_url else "Text-to-Image (/draw)"
    await notify_admin_activity(context, user, act_name, prompt)

    status_msg = await update.message.reply_text(
        f"🎨 *Menyiapkan Studio Gambar...*\n⏳ _Memeriksa antrean GPU cluster..._",
        reply_markup=cancel_button_keyboard(),
        parse_mode="Markdown"
    )

    async def _queue_cb(wait_pos: int, est_sec: int):
        await status_msg.edit_text(
            f"⏳ *Antrean Studio #{wait_pos}*\n"
            f"Ada tugas lain yang sedang diproses GPU. Estimasi giliran: ~{est_sec} detik...",
            reply_markup=cancel_button_keyboard(),
            parse_mode="Markdown"
        )

    def on_live_progress(status_text: str, elapsed_sec: int, percent: int):
        bar = generate_progress_bar(percent, total_blocks=10)
        msg_text = f"🎨 Generating *{ratio}* · *{percent}%*\n`{bar}`\n⏱️ {elapsed_sec}s · _{status_text}_"
        asyncio.run_coroutine_threadsafe(
            status_msg.edit_text(msg_text, reply_markup=cancel_button_keyboard(), parse_mode="Markdown"),
            loop
        )

    async def _core_render():
        t0 = time.time()
        from services.image_fallback_service import generate_image_with_fallback
        res = await asyncio.to_thread(
            generate_image_with_fallback, 
            prompt, 
            style_key=st["image_style"], 
            ratio_key=ratio, 
            progress_cb=on_live_progress
        )
        elapsed = int(time.time() - t0)

        if res["success"]:
            # Record analytics for image generation
            track_usage(
                user_id=uid,
                user_name=user.first_name,
                username=user.username,
                action="edit_img" if ref_url else "draw",
                model_id=res.get("cluster_used", "Qwen Image MCP"),
                prompt_tokens=len(prompt.split()) * 2,
                completion_tokens=0,
                is_fallback=res.get("fallback_used", False)
            )

            final_bar = generate_progress_bar(100, total_blocks=10)
            cluster_info = res.get("cluster_used", "Qwen Image MCP")
            final_status = f"🎨 Generating *{ratio}* · *100%*\n`{final_bar}`\n⏱️ {elapsed}s · _Selesai! ({cluster_info})_"
            try:
                await status_msg.edit_text(final_status, parse_mode="Markdown")
            except Exception:
                pass

            caption = (
                f"✅ *Prompt:* {prompt}\n"
                f"🎭 *Gaya:* `{res['style']}` | 📐 *Rasio:* `{res['ratio']}`\n"
                f"⚡ *Engine:* `{cluster_info}` ({res['latency']})"
            )
            await update.message.reply_photo(photo=res["image_url"], caption=caption, parse_mode="Markdown")
            await update.message.reply_text("Mau generate lagi? 👇", reply_markup=after_generate_keyboard())
        else:
            await status_msg.edit_text(f"❌ Gagal merender gambar: {res['error']}", reply_markup=after_generate_keyboard())

    async def _runner():
        from services.queue_service import run_in_queue
        await run_in_queue(_queue_cb, _core_render, estimated_job_seconds=25)

    task = asyncio.create_task(_runner())
    active_user_tasks[uid] = task
    try:
        await task
    except asyncio.CancelledError:
        try:
            await status_msg.edit_text("🛑 *Generasi gambar dibatalkan.*", reply_markup=after_generate_keyboard(), parse_mode="Markdown")
        except Exception:
            pass
    finally:
        active_user_tasks.pop(uid, None)


# ─────────────────────────────────────────────────────────────
# 4. COMMAND HANDLERS
# ─────────────────────────────────────────────────────────────
async def browse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = " ".join(context.args) if context.args else ""
    if not url:
        uid = update.effective_user.id
        st = get_user_state(uid)
        st["waiting_for"] = "browser_url"
        await update.message.reply_text("🌐 *Silakan kirimkan alamat website yang ingin dibuka:* \n(Contoh: `classroom.itats.ac.id` atau `github.com`)", parse_mode="Markdown")
        return
    await execute_browser_task(update, context, raw_url=url)


async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args) if context.args else ""
    if not prompt:
        uid = update.effective_user.id
        st = get_user_state(uid)
        st["waiting_for"] = "draw_prompt"
        await update.message.reply_text("🎨 *Silakan kirimkan deskripsi gambar yang ingin dibuat:*", parse_mode="Markdown")
        return
    await execute_image_generation(update, context, prompt=prompt)


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    task = active_user_tasks.get(uid)
    if task and not task.done():
        task.cancel()
        await update.message.reply_text("🛑 *Proses berhasil dihentikan (Stopped)!*", parse_mode="Markdown")
    else:
        await update.message.reply_text("ℹ️ Tidak ada proses yang sedang berjalan.", parse_mode="Markdown")


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    clear_user_memory(uid)
    await update.message.reply_text("🧹 *Riwayat percakapan Anda telah dibersihkan (Memory Reset)!*", parse_mode="Markdown")


async def persona_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text("🎭 *PILIH PERSONA KOGNITIF & GODMODE:*", reply_markup=personas_keyboard(uid), parse_mode="Markdown")


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text("⚙️ *PENGATURAN STUDIO GAMBAR:*", reply_markup=settings_keyboard(uid), parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚙️ *STATUS CLUSTER & INFRASTRUKTUR:* \n\n"
        "🟢 *HF Router (138 Models):* Online\n"
        "🟢 *MCP Image Cluster:* Online (Uncensored)\n"
        "🟢 *Live Browser (Playwright):* Active\n"
        "🟢 *Memory & RAG Engine:* Active\n"
        "🟢 *Multi-Tier Fallback:* 9 Layer Protection"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─────────────────────────────────────────────────────────────
# 5. PHOTO & TEXT MESSAGE HANDLERS
# ─────────────────────────────────────────────────────────────
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = get_user_state(uid)
    photo_file = await update.message.photo[-1].get_file()
    st["ref_photo_url"] = photo_file.file_path
    st["waiting_for"] = "edit_prompt"

    caption = update.message.caption
    if caption:
        await execute_image_generation(update, context, prompt=caption, ref_url=photo_file.file_path)
    else:
        text = (
            "🖼️ *Foto Referensi Diterima!*\n\n"
            "Sekarang kirimkan instruksi perubahannya.\n"
            "💡 *Contoh:* `ubah background jadi kota cyberpunk malam hari`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return
    uid = update.effective_user.id
    st = get_user_state(uid)

    # 1. State: Menunggu URL Browser
    if st["waiting_for"] == "browser_url":
        st["waiting_for"] = None
        await execute_browser_task(update, context, raw_url=user_text)
        return

    # 2. State: Menunggu Prompt Gambar
    if st["waiting_for"] == "draw_prompt":
        st["waiting_for"] = None
        await execute_image_generation(update, context, prompt=user_text)
        return

    # 3. State: Menunggu Prompt Edit Foto
    if st["waiting_for"] == "edit_prompt":
        st["waiting_for"] = None
        await execute_image_generation(update, context, prompt=user_text, ref_url=st.get("ref_photo_url"))
        return

    # 4. Mode Chat / Kategori
    user = update.effective_user
    cat_info = HF_OFFICIAL_CATEGORIES.get(st["category"], HF_OFFICIAL_CATEGORIES["chatbots"])
    p_info = PERSONAS.get(st["persona"], PERSONAS["hermes"])
    
    # Notif Chat Prompt ke Admin
    await notify_admin_activity(context, user, f"Chat LLM ({p_info['name'].split()[0]})", user_text)

    status_msg = await update.message.reply_text(
        f"⏳ *{p_info['name'].split()[0]} sedang memproses...*",
        reply_markup=cancel_button_keyboard(),
        parse_mode="Markdown"
    )

    async def _chat_runner():
        res = await asyncio.to_thread(
            ask_llm, 
            user_text, 
            user_id=uid, 
            preferred_model_id=p_info["model_id"], 
            system_prompt=p_info["sys_prompt"]
        )
        if res["success"]:
            # Record Analytics
            track_usage(
                user_id=uid,
                user_name=user.first_name,
                username=user.username,
                action="chat",
                model_id=res.get("model"),
                prompt_tokens=res.get("prompt_tokens", 0),
                completion_tokens=res.get("completion_tokens", 0),
                is_fallback=res.get("fallback_used", False)
            )
            
            fb_tag = " 🔄 *(Auto-Fallback ke Backup Engine)*" if res.get("fallback_used") else ""
            footer = f"\n\n🤖 *Model Penjawab:* `{res['model']}`{fb_tag}\n⚡ *Latency:* `{res['latency']}`"
            reply = f"{res['response']}{footer}"
            if len(reply) > 4000:
                for chunk in [reply[i:i+4000] for i in range(0, len(reply), 4000)]:
                    await update.message.reply_text(chunk)
                await status_msg.delete()
            else:
                await status_msg.edit_text(reply)
        else:
            await status_msg.edit_text(f"❌ Error: {res['error']}")

    task = asyncio.create_task(_chat_runner())
    active_user_tasks[uid] = task
    try:
        await task
    except asyncio.CancelledError:
        try:
            await status_msg.edit_text("🛑 *Proses chat dibatalkan.*", parse_mode="Markdown")
        except Exception:
            pass
    finally:
        active_user_tasks.pop(uid, None)


# ─────────────────────────────────────────────────────────────
# 6. CALLBACK QUERY ROUTER (TOMBOL INTERAKTIF)
# ─────────────────────────────────────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = query.from_user.id
    st = get_user_state(uid)

    # ── ADMIN PANEL DASHBOARD ──
    if data == "nav_admin_panel":
        if uid != ADMIN_ID:
            await query.edit_message_text("⛔ *Akses Ditolak:* Menu ini khusus Administrator.", parse_mode="Markdown")
            return
        
        summary = get_analytics_summary()
        text = (
            "👑 *DASBOR ADMINISTRATOR & USAGE METRICS*\n\n"
            f"⏱️ *Bot Uptime:* `{summary['uptime']}`\n"
            f"👥 *Total Pengguna Unik:* `{summary['unique_users_count']}` user\n"
            f"📊 *Total Request:* `{summary['total_requests']}` requests\n"
            f"🪙 *Total Estimasi Token:* `{summary['total_tokens_est']:,}` tokens\n\n"
            "📈 *Breakdown Aktivitas:*\n"
            f"• 💬 Chat LLM: `{summary['action_breakdown'].get('chat', 0)}`\n"
            f"• 🎨 Generate Gambar: `{summary['action_breakdown'].get('draw', 0)}`\n"
            f"• 🖼️ Edit Foto: `{summary['action_breakdown'].get('edit_img', 0)}`\n"
            f"• 🌐 Live Browser: `{summary['action_breakdown'].get('browser', 0)}`"
        )
        buttons = [
            [
                InlineKeyboardButton("🏆 Ranking Model Terpopuler", callback_data="admin_view_models"),
                InlineKeyboardButton("👥 Top Active Users", callback_data="admin_view_users")
            ],
            [
                InlineKeyboardButton("🔄 Refresh Data", callback_data="nav_admin_panel"),
                InlineKeyboardButton("🔙 Menu Utama", callback_data="nav_main")
            ]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data == "admin_view_models":
        if uid != ADMIN_ID:
            return
        summary = get_analytics_summary()
        top_models = summary["top_models"]
        
        text = "🏆 *RANKING & PENGGUNAAN MODEL AI:*\n\n"
        if not top_models:
            text += "_Belum ada data penggunaan model._"
        else:
            for idx, (m_id, m_data) in enumerate(top_models, 1):
                text += (
                    f"*{idx}. `{m_id}`*\n"
                    f"   • Dipanggil: `{m_data['calls']}` kali\n"
                    f"   • Est. Tokens: `{m_data['tokens_est']:,}`\n"
                    f"   • Auto-Fallback: `{m_data.get('fallbacks', 0)}` kali\n\n"
                )
        buttons = [
            [InlineKeyboardButton("🔙 Kembali ke Dasbor Admin", callback_data="nav_admin_panel")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data == "admin_view_users":
        if uid != ADMIN_ID:
            return
        summary = get_analytics_summary()
        top_users = summary["top_users"]
        
        text = "👥 *LEADERBOARD AKTIVITAS PENGGUNA:*\n\n"
        if not top_users:
            text += "_Belum ada interaksi user yang tercatat._"
        else:
            for idx, (u_id, u_data) in enumerate(top_users, 1):
                text += (
                    f"*{idx}. {u_data['name']}* (`@{u_data['username']}`) [ID: `{u_id}`]\n"
                    f"   • Total Aksi: `{u_data['calls']}` kali\n"
                    f"   • Terakhir Aktif: `{u_data['last_seen']}`\n\n"
                )
        buttons = [
            [InlineKeyboardButton("🔙 Kembali ke Dasbor Admin", callback_data="nav_admin_panel")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    # ── STOP PROSES DARI TOMBOL ──
    if data == "btn_stop_process":
        task = active_user_tasks.get(uid)
        if task and not task.done():
            task.cancel()
            await query.edit_message_text("🛑 *Proses berhasil dibatalkan dari tombol!*", parse_mode="Markdown")
        else:
            await query.edit_message_text("ℹ️ Proses sudah selesai atau tidak ada yang aktif.", parse_mode="Markdown")

    elif data == "nav_main":
        p_info = PERSONAS.get(st["persona"], PERSONAS["hermes"])
        text = (
            f"👑 *HUGGING FACE MULTI-AI HUB v6.0*\n\n"
            f"🪽 *Persona:* `{p_info['icon']} {p_info['name']}`\n"
            f"🎨 *Preset:* `{st['image_style'].title()}` ({st['image_ratio']})\n\n"
            "Pilih opsi di bawah:"
        )
        await query.edit_message_text(text, reply_markup=main_dashboard_keyboard(uid), parse_mode="Markdown")

    elif data == "action_browser_flow":
        st["waiting_for"] = "browser_url"
        text = (
            "🌐 *LIVE BROWSER AUTOMATION*\n\n"
            "Silakan ketik atau kirimkan alamat website yang ingin Anda buka & ambil screenshotnya sekarang:\n\n"
            "💡 *Contoh:* `classroom.itats.ac.id` atau `github.com`"
        )
        buttons = [[InlineKeyboardButton("🔙 Batal & Menu Utama", callback_data="nav_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data == "action_draw_flow":
        st["waiting_for"] = "draw_prompt"
        text = (
            "🎨 *STUDIO BIKIN GAMBAR HD*\n\n"
            f"⚙️ *Gaya Aktif:* `{st['image_style'].title()}` | 📐 *Rasio:* `{st['image_ratio']}`\n\n"
            "Silakan ketikkan deskripsi gambar yang ingin dibuat sekarang:\n\n"
            "💡 *Contoh:* `a futuristic cyberpunk supercar racing on neon highway`"
        )
        buttons = [
            [InlineKeyboardButton("⚙️ Ubah Gaya / Rasio", callback_data="nav_settings")],
            [InlineKeyboardButton("🔙 Batal & Menu Utama", callback_data="nav_main")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data == "action_edit_img":
        st["waiting_for"] = "edit_prompt"
        text = (
            "🖼️ *MODE EDIT FOTO / IMAGE-TO-IMAGE*\n\n"
            "Silakan **kirimkan sebuah foto** ke chat ini, lalu tambahkan teks perubahan yang diinginkan pada captionnya!"
        )
        buttons = [[InlineKeyboardButton("🔙 Menu Utama", callback_data="nav_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data == "btn_reset_memory":
        clear_user_memory(uid)
        await query.edit_message_text("🧹 *Ingatan riwayat percakapan Anda telah dibersihkan!*", reply_markup=main_dashboard_keyboard(uid), parse_mode="Markdown")

    elif data == "nav_personas":
        text = "🎭 *PILIH PERSONA KOGNITIF & GODMODE:*"
        await query.edit_message_text(text, reply_markup=personas_keyboard(uid), parse_mode="Markdown")

    elif data.startswith("set_persona:"):
        pk = data.split(":")[1]
        st["persona"] = pk
        p = PERSONAS.get(pk, {})
        st["model_id"] = p["model_id"]
        st["model_name"] = p["name"]
        
        text = (
            f"✅ *Persona Diaktifkan: {p['icon']} {p['name']}*\n\n"
            f"💡 *Karakteristik:* {p['desc']}\n\n"
            "Semua interaksi Anda berikutnya akan dijawab menggunakan persona ini."
        )
        buttons = [
            [InlineKeyboardButton("🚀 Lanjut Chat", callback_data="nav_main")],
            [InlineKeyboardButton("🔙 Ganti Persona Lain", callback_data="nav_personas")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data == "nav_categories":
        text = "📂 *KATALOG 28 KATEGORI RESMI HUGGING FACE:*\n\nPilih filter mode di bawah:"
        await query.edit_message_text(text, reply_markup=all_categories_keyboard("all"), parse_mode="Markdown")

    elif data.startswith("filter_cat:"):
        ftype = data.split(":")[1]
        label = "✨ Semua Kategori" if ftype == "all" else ("🔞 Mode Uncensored" if ftype == "uncensored" else "🛡️ Mode Standard")
        text = f"📂 *KATALOG HUGGING FACE — {label}*\n\nSilakan pilih salah satu kategori:"
        await query.edit_message_text(text, reply_markup=all_categories_keyboard(ftype), parse_mode="Markdown")

    elif data.startswith("select_cat:"):
        cat_key = data.split(":")[1]
        st["category"] = cat_key
        cat = HF_OFFICIAL_CATEGORIES.get(cat_key, {})
        
        if cat_key == "live_browser":
            st["waiting_for"] = "browser_url"
            text = "🌐 *Kategori Live Browser:* Kirimkan URL web yang ingin dibuka!"
        elif cat_key == "text_to_image":
            st["waiting_for"] = "draw_prompt"
            text = "🎨 *Kategori Gambar:* Kirimkan deskripsi gambar yang ingin dibuat!"
        else:
            text = f"✅ *Kategori: {cat['icon']} {cat['name']}*\n\n💡 {cat['desc']}\n\nLangsung ketik pesan teks Anda!"

        buttons = [
            [InlineKeyboardButton("🚀 Mulai", callback_data="nav_main")],
            [InlineKeyboardButton("🔙 Kategori Lain", callback_data="nav_categories")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown", disable_web_page_preview=True)

    elif data == "nav_settings":
        await query.edit_message_text("⚙️ *PENGATURAN STUDIO GAMBAR:*", reply_markup=settings_keyboard(uid), parse_mode="Markdown")

    elif data == "choose_style":
        buttons = []
        for sk in IMAGE_STYLES.keys():
            check = "✅ " if st["image_style"] == sk else ""
            buttons.append([InlineKeyboardButton(f"{check}{sk.replace('_',' ').title()}", callback_data=f"set_style:{sk}")])
        buttons.append([InlineKeyboardButton("🔙 Kembali ke Setting", callback_data="nav_settings")])
        await query.edit_message_text("🎭 *Pilih Gaya Visual Gambar:*", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data.startswith("set_style:"):
        st["image_style"] = data.split(":")[1]
        await query.edit_message_text("✅ Gaya visual berhasil diubah!", reply_markup=settings_keyboard(uid), parse_mode="Markdown")

    elif data == "choose_ratio":
        buttons = []
        for rk, robj in ASPECT_RATIOS.items():
            check = "✅ " if st["image_ratio"] == rk else ""
            buttons.append([InlineKeyboardButton(f"{check}{robj['name']}", callback_data=f"set_ratio:{rk}")])
        buttons.append([InlineKeyboardButton("🔙 Kembali ke Setting", callback_data="nav_settings")])
        await query.edit_message_text("📐 *Pilih Aspek Rasio Kanvas:*", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data.startswith("set_ratio:"):
        st["image_ratio"] = data.split(":")[1]
        await query.edit_message_text("✅ Rasio kanvas berhasil diubah!", reply_markup=settings_keyboard(uid), parse_mode="Markdown")

    elif data == "nav_status":
        text = (
            "⚙️ *STATUS CLUSTER & INFRASTRUKTUR:* \n\n"
            "🟢 *HF Router (138 Models):* Online\n"
            "🟢 *MCP Image Cluster:* Online (Uncensored)\n"
            "🟢 *Live Browser (Playwright):* Active\n"
            "🟢 *Interactive Buttons & Commands:* Synchronized\n"
            "🟢 *Multi-Tier Fallback:* 9 Layer Protection"
        )
        buttons = [[InlineKeyboardButton("🔙 Menu Utama", callback_data="nav_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")


def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(register_bot_commands)
        .build()
    )
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", start_command))
    app.add_handler(CommandHandler("draw", draw_command))
    app.add_handler(CommandHandler("browse", browse_command))
    app.add_handler(CommandHandler("persona", persona_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("cancel", stop_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    print("🚀 [V6.0 DUAL-MODE] Telegram Bot @myHF_gateway_bot berjalan dengan Full Tombol & Alur Step-by-Step!")
    app.run_polling()

if __name__ == "__main__":
    main()
