from PyroUbot import *
from PyroUbot.core.helpers import PY
from pyrogram import enums
from pyrogram.types import Message
import psutil

__MODULE__ = "ʀᴇꜱᴏᴜʀᴄᴇ"

@PY.UBOT("resource")
async def _(client, message: Message):
    cpu = psutil.cpu_percent(percpu=True)
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()

    text = "<b>📊 RESOURCE DETAIL</b><blockquote>"
    for i, c in enumerate(cpu):
        text += f"\nCPU Core {i+1}: {c}%"
    text += f"""
    
RAM Free : {ram.available//1024**2} MB
Swap Used : {swap.used//1024**2} MB
</blockquote>
"""
    await message.reply(text, parse_mode=enums.ParseMode.HTML)