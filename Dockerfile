# 1. Base Image dengan Python 3.10
FROM python:3.10-slim

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# 2. Install sistem dependensi untuk Chromium & Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    ca-certificates \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    fonts-liberation \
    libappindicator3-1 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 3. Copy & install dependencies Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Install browser Chromium Playwright
RUN python -m playwright install chromium

# 5. Copy seluruh kode aplikasi
COPY . .

# 6. Buat folder data persisten
RUN mkdir -p /app/data/screenshots

# 7. Jalankan bot
CMD ["python", "bot.py"]
