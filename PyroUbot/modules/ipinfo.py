from PyroUbot import *
from PyroUbot.core.helpers import PY
from pyrogram.types import Message
from pyrogram import enums
import socket
import subprocess

__MODULE__ = "ɴᴇᴛᴛᴏᴏʟꜱ"

__HELP__ = """
<b>⦪ ɴᴇᴛᴡᴏʀᴋ ᴛᴏᴏʟꜱ ⦫</b>

<blockquote>ᚗ <code>{0}ip</code> domain
ᚗ <code>{0}ping</code> host</blockquote>

<b>Contoh:</b>
<code>{0}ip google.com</code>
<code>{0}ping 8.8.8.8</code>
"""

@PY.UBOT("ip")
async def _(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("Gunakan: <code>ip google.com</code>")

    domain = message.command[1]

    try:
        ip = socket.gethostbyname(domain)
        await message.reply(
            f"<b>🌐 IP DOMAIN</b>\n<blockquote>{domain} → <code>{ip}</code></blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await message.reply(f"❌ Gagal resolve domain\n<code>{e}</code>")

@PY.UBOT("ping")
async def _(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("Gunakan: <code>ping google.com</code>")

    host = message.command[1]

    try:
        result = subprocess.check_output(
            ["ping", "-c", "3", host],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=10
        )

        await message.reply(
            f"<b>📡 PING RESULT</b>\n<pre>{result}</pre>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        await message.reply("❌ Host tidak merespon / diblokir")