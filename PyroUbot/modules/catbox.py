from pyrogram import Client
import requests
import os
import time as _time

from PyroUbot import *

__MODULE__ = "ᴄᴀᴛʙᴏx"
__HELP__ = """
<blockquote><b>Catbox Uploader</b>

<b>Command:</b>
<code>{0}catbox</code>
<code>{0}litterbox</code>

<b>Cara pakai:</b>
• Reply ke foto / video / file
• Ketik command di atas</blockquote>
"""

CATBOX_API = "https://catbox.moe/user/api.php"


def progress_bar(current, total):
    percent = current * 100 / total if total else 0
    filled = int(percent / 10)
    return f"[{'█'*filled}{'░'*(10-filled)}] {percent:.1f}%"


async def download_progress(current, total, message, start):
    if _time.time() - start < 1:
        return
    try:
        await message.edit(
            "<b>📥 Downloading...</b>\n"
            f"<code>{progress_bar(current, total)}</code>"
        )
    except:
        pass


async def upload_catbox(file_path, temporary=False):
    data = {"reqtype": "fileupload"}
    if temporary:
        data = {"reqtype": "litterbox", "time": "1h"}

    with open(file_path, "rb") as f:
        r = requests.post(
            CATBOX_API,
            data=data,
            files={"fileToUpload": f},
            timeout=60,
        )

    if r.status_code == 200 and r.text.startswith("https://"):
        return r.text
    return None


@PY.UBOT("catbox")
@PY.UBOT("litterbox")
async def catbox_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply("❌ Reply ke media")

    temporary = message.command == "litterbox"
    status = await message.reply("📥 Downloading...")
    start = _time.time()

    file_path = await client.download_media(
        message.reply_to_message,
        progress=download_progress,
        progress_args=(status, start),
    )

    await status.edit("📤 Uploading ke Catbox...")

    url = await upload_catbox(file_path, temporary)
    if not url:
        return await status.edit("❌ Upload gagal")

    await status.edit(
        "<b>✅ UPLOAD BERHASIL</b>\n\n"
        f"<code>{url}</code>",
        disable_web_page_preview=True,
    )

    try:
        os.remove(file_path)
    except:
        pass