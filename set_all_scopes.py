import asyncio, os
from dotenv import load_dotenv
from telegram import Bot, BotCommand, BotCommandScopeDefault, BotCommandScopeAllPrivateChats

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

async def main():
    bot = Bot(token=TOKEN)
    commands = [
        BotCommand("start", "🚀 Buka menu utama & dasbor AI"),
        BotCommand("menu", "📂 Buka katalog 28 kategori AI Hugging Face"),
        BotCommand("draw", "🎨 Generate gambar HD bebas sensor"),
        BotCommand("browse", "🌐 Buka website live & ambil screenshot"),
        BotCommand("persona", "🎭 Ganti persona (Hermes / Jev / Coder / R1)"),
        BotCommand("stop", "🛑 Batalkan tugas yang sedang berjalan"),
        BotCommand("reset", "🧹 Hapus ingatan chat (Reset Memory)"),
        BotCommand("settings", "⚙️ Atur rasio kanvas & gaya gambar"),
        BotCommand("status", "⚡ Cek status server cluster AI")
    ]
    
    # 1. Scope Default
    r1 = await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    print(f"Scope Default: {r1}")
    
    # 2. Scope All Private Chats (Khusus DM Chat Pribadi)
    r2 = await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())
    print(f"Scope All Private Chats: {r2}")
    
    # Verifikasi apa yang tersimpan
    active_cmds = await bot.get_my_commands()
    print("Daftar command tersimpan di Telegram server:")
    for c in active_cmds:
        print(f"  /{c.command} - {c.description}")

if __name__ == "__main__":
    asyncio.run(main())
