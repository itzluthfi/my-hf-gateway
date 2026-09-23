# 🚀 Panduan Deploy Hugging Face Gateway Bot ke Server VPS

Panduan deployment satu langkah ke VPS Linux (Ubuntu / Debian / Docker / Systemd).

---

## 📦 1. Deploy via Docker Compose (Paling Direkomendasikan)

Pastikan Docker & Docker Compose sudah terpasang di VPS Anda.

1. **Clone / Upload folder ke VPS:**
   ```bash
   scp -r d:/FREELANCE/huggingface-gateway root@<IP_VPS>:/root/
   ```

2. **Masuk ke direktori dan cek file `.env`:**
   ```bash
   cd /root/huggingface-gateway
   nano .env
   ```
   Pastikan berisi:
   ```env
   HF_TOKEN=your_huggingface_token_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_ID=your_telegram_id_here
   ```

3. **Jalankan Bot di Background (Auto-Restart On Crash):**
   ```bash
   docker compose up -d --build
   ```

4. **Cek Log Bot:**
   ```bash
   docker compose logs -f
   ```

---

## ⚙️ 2. Deploy via Systemd Service (Tanpa Docker)

Jika ingin menjalankan langsung di Python host VPS:

1. **Install dependensi di VPS:**
   ```bash
   apt-get update && apt-get install -y python3-pip python3-venv
   cd /root/huggingface-gateway
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install --with-deps chromium
   ```

2. **Buat file service systemd:**
   ```bash
   nano /etc/systemd/system/hfgateway.service
   ```
   Paste konfigurasi berikut:
   ```ini
   [Unit]
   Description=Hugging Face Multi-AI Gateway Bot
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/root/huggingface-gateway
   ExecStart=/root/huggingface-gateway/venv/bin/python bot.py
   Restart=always
   RestartSec=5
   EnvironmentFile=/root/huggingface-gateway/.env

   [Install]
   WantedBy=multi-user.target
   ```

3. **Aktifkan & Jalankan Service:**
   ```bash
   systemctl daemon-reload
   systemctl enable hfgateway
   systemctl start hfgateway
   systemctl status hfgateway
   ```
