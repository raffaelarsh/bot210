from PyroUbot import *
import random
import requests
from pyrogram.enums import ChatAction, ParseMode
from pyrogram import filters
from pyrogram.types import Message

__MODULE__ = "ᴀᴏʏᴏ"
__HELP__ = """
<blockquote><b>Bantuan Untuk aoyo

perintah : <code>{0}aoyo</code>
    Membantu mencari informasi dengan nama, contoh: .aoyo informasi siapa Boysz</b></blockquote>
"""


@PY.UBOT("aoyo")
@PY.TOP_CMD
async def chat_gpt(client, message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)

        if len(message.command) < 2:
            await message.reply_text(
                "<emoji id=5019523782004441717>❌</emoji>mohon gunakan format\ncontoh : .aoyo cari informasi siapa Boysz"
            )
        else:
            prs = await message.reply_text(f"<emoji id=5469783727838088134>💻</emoji>proccesing mencari informasi....")
            a = message.text.split(' ', 1)[1]
            response = requests.get(f'https://api.siputzx.my.id/api/ai/aoyo?content={a}')

            try:
                if "data" in response.json():
                    x = response.json()["data"]                  
                    await prs.edit(
                      f"<blockquote>{x}</blockquote>"
                    )
                else:
                    await message.reply_text("No 'results' key found in the response.")
            except KeyError:
                await message.reply_text("Error accessing the response.")
    except Exception as e:
        await message.reply_text(f"{e}")
