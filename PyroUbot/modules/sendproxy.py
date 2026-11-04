import requests
import asyncio
from pyrogram import Client, filters
from pyrogram import *
from PyroUbot import PY

__MODULE__ = "sᴇɴᴅ ᴘʀᴏxʏ"
__HELP__ = """
<blockquote><b>Bantuan Untuk Auto Proxy</b>

Perintah: <code>{0}proxy</code>
Penjelasan: Mengirimkan daftar proxy terbaru dan memperbaruinya setiap 3 menit.</blockquote></b>
"""

# URL sumber proxy (pastikan mengganti dengan sumber proxy yang valid)
PROXY_URL = "https://api.proxyscrape.com/?request=displayproxies&proxytype=http"

# Dictionary untuk menyimpan data proxy
latest_proxies = []

async def update_proxies():
    global latest_proxies
    while True:
        try:
            response = requests.get(PROXY_URL)
            if response.status_code == 200:
                latest_proxies = response.text.strip().split("\n")
        except Exception as e:
            print(f"⚠️ Gagal memperbarui proxy: {e}")
        await asyncio.sleep(5)  # Tunggu 3 menit sebelum memperbarui lagi

@PY.UBOT("proxy")
@PY.TOP_CMD
async def send_proxy_command(client, message):
    if not latest_proxies:
        await message.reply_text("❌ Proxy belum tersedia atau gagal diperbarui.")
        return

    proxy_list = "\n".join(latest_proxies[:100])  # Ambil 5 proxy terbaru
    result_text = f"🔹 **Proxy Terbaru (Update Tiap 3 Menit)** 🔹\n\n<blockquote><b>{proxy_list}</b></blockquote>"
    await message.reply_text(result_text)

# Jalankan fungsi update proxy di background
loop = asyncio.get_event_loop()
loop.create_task(update_proxies())