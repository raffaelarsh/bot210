from PyroUbot import *
from PyroUbot.core.helpers import PY
from pyrogram.types import Message
from pyrogram import enums
import psutil

__MODULE__ = "ᴘʀᴏᴄᴇꜱꜱ"

__HELP__ = """
<b>⦪ ᴘʀᴏᴄᴇꜱꜱ ᴍᴏɴɪᴛᴏʀ ⦫</b>

<blockquote>
ᚗ <code>{0}ps</code>
⊷ Menampilkan process paling berat
</blockquote>
"""

@PY.UBOT("ps")
async def _(client, message: Message):
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        procs.append(p.info)

    top = sorted(procs, key=lambda x: x['cpu_percent'], reverse=True)[:5]

    text = "<b>🔥 TOP PROCESS</b>\n<blockquote>"
    for p in top:
        text += f"\n• {p['name']} | CPU {p['cpu_percent']}% | RAM {p['memory_percent']:.1f}%"
    text += "</blockquote>"

    await message.reply(text, parse_mode=enums.ParseMode.HTML)