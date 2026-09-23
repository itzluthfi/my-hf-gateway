"""
services/browser_service.py — Live Headless Browser Engine (Playwright) dengan Smart URL Parser
Fitur:
• Smart URL Extractor (Bisa membedakan instruksi teks vs alamat domain URL)
• Fallback screenshot jika networkidle timeout pada website berat
• Cancel/Abort Task Support
"""
import os, time, re, asyncio
from playwright.async_api import async_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Regex extractor URL atau domain (misal: classroom.itats.ac.id atau https://...)
URL_REGEX = re.compile(
    r'(https?://[^\s]+|[a-zA-Z0-9.-]+\.(?:com|org|net|id|ac\.id|go\.id|co\.id|io|ai|me|app|dev|edu|site|shop|space)(?:/[^\s]*)?)',
    re.IGNORECASE
)

def extract_clean_url(raw_input: str) -> str:
    """Mengekstrak URL valid dari kalimat input user yang bercampur instruksi."""
    match = URL_REGEX.search(raw_input)
    if match:
        url = match.group(1).strip().rstrip('/')
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        return url
    # Jika tidak ada domain terdeteksi, bersihkan spasi
    cleaned = raw_input.strip()
    if not cleaned.startswith("http://") and not cleaned.startswith("https://"):
        cleaned = "https://" + cleaned
    return cleaned


async def browse_and_capture(raw_input: str) -> dict:
    """Membuka URL dengan browser Chromium, merender DOM, dan mengambil screenshot."""
    clean_url = extract_clean_url(raw_input)
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"shot_{int(time.time())}.png")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            t0 = time.time()
            # Coba navigasi dengan timeout 20s
            try:
                response = await page.goto(clean_url, wait_until="load", timeout=20000)
            except Exception:
                # Jika load timeout, tetap lanjutkan untuk render DOM yang sudah ada
                response = None

            # Tunggu rendering selesai
            await page.wait_for_timeout(2000)
            elapsed = time.time() - t0
            
            title = await page.title()
            try:
                text_content = await page.evaluate("() => document.body.innerText.substring(0, 1000)")
            except Exception:
                text_content = "Tidak dapat mengekstrak teks."
            
            await page.screenshot(path=screenshot_path, full_page=False)
            await browser.close()
            
            return {
                "success": True,
                "url": clean_url,
                "title": title or clean_url,
                "status_code": response.status if response else 200,
                "text_snippet": text_content.strip() if text_content else "",
                "screenshot_path": screenshot_path,
                "latency": f"{elapsed:.2f}s"
            }
    except Exception as e:
        return {
            "success": False,
            "url": clean_url,
            "error": str(e)
        }
