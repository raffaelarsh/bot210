from PyroUbot import *
from PyroUbot.core.helpers import PY
from pyrogram.types import Message
from pyrogram import enums
import platform
import psutil
import time

__MODULE__ = "sᴇʀᴠᴇʀ"

__HELP__ = """
<b>⦪ ꜱᴇʀᴠᴇʀ ɪɴꜰᴏ ⦫</b>

<blockquote>ᚗ <code>{0}server</code>
⊷ Menampilkan info VPS / hosting</blockquote>
"""

@PY.UBOT("server")
async def _(client, message: Message):
    boot = time.time() - psutil.boot_time()
    uptime = time.strftime("%H jam %M menit", time.gmtime(boot))

    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    text = f"""
<b>🖥 SERVER INFO</b>

<blockquote>
• OS : <code>{platform.system()} {platform.release()}</code>
• CPU : <code>{cpu}%</code>
• RAM : <code>{ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB</code>
• Disk : <code>{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB</code>
• Uptime : <code>{uptime}</code>
• Python : <code>{platform.python_version()}</code>
</blockquote>
"""

    await message.reply(text, parse_mode=enums.ParseMode.HTML)