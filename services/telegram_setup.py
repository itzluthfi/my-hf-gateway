"""
services/telegram_setup.py — Mendaftarkan Menu Command List Resmi ke BotFather/Telegram API
Termasuk tombol /stop /cancel untuk membatalkan proses yang sedang berjalan.
"""
from telegram import BotCommand

async def register_bot_commands(app):
    """Mendaftarkan menu tombol slash '/' resmi di Telegram."""
    commands = [
        BotCommand("start", "🚀 Buka menu utama & dasbor AI"),
        BotCommand("menu", "📂 Buka katalog 28 kategori AI Hugging Face"),
        BotCommand("draw", "🎨 Generate gambar HD bebas sensor (/draw <prompt>)"),
        BotCommand("browse", "🌐 Buka website live & ambil screenshot (/browse <url>)"),
        BotCommand("persona", "🎭 Ganti persona (Hermes / Jev / Coder / R1)"),
        BotCommand("stop", "🛑 Batalkan tugas/proses yang sedang berjalan"),
        BotCommand("reset", "🧹 Hapus riwayat ingatan chat (Reset Memory)"),
        BotCommand("settings", "⚙️ Atur rasio kanvas & gaya visual gambar"),
        BotCommand("status", "⚡ Cek status server cluster AI & fallback")
    ]
    try:
        await app.bot.set_my_commands(commands)
        print("✅ [TELEGRAM] 9 Menu Perintah '/' Resmi Berhasil Didaftarkan ke Telegram API!")
    except Exception as e:
        print(f"⚠️ Gagal mendaftarkan bot commands: {e}")
