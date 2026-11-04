from pyrogram import Client, filters
from pyrogram.types import Message
import requests

API_KEY = "https://api.neoxr.my.id/api/tiktoksearch"

@Client.on_message(filters.command("ttsearch", prefixes=".") & filters.me)
async def tiktok_search(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.edit("❌ Masukkan kata kunci.\nContoh: `.ttsearch kucing lucu`")

    query = " ".join(message.command[1:])
    await message.edit("🔍 Mencari video TikTok...")

    try:
        res = requests.get(
            "https://api.neoxr.my.id/api/tiktoksearch",
            params={"query": query, "apikey": API_KEY}
        )
        data = res.json()

        if res.status_code == 200 and data.get("status") and data.get("data"):
            video_data = data["data"][0]  # Ambil video pertama dari hasil
            video_url = video_data.get("url", "")
            desc = video_data.get("title", "Tanpa judul")
            author = video_data.get("author", {}).get("nickname", "Unknown")

            await message.edit(
                f"🎬 **Hasil Pencarian TikTok**\n\n"
                f"👤 **Author**: {author}\n"
                f"📄 **Deskripsi**: {desc}\n"
                f"🔗 **Link**: [Tonton Video]({video_url})",
                disable_web_page_preview=False
            )
        else:
            await message.edit("❌ Tidak ditemukan atau API error.")
    except Exception as e:
        await message.edit(f"⚠️ Terjadi error:\n`{e}`")