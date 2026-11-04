from PyroUbot import *
import random
import requests
import os
from pyrogram.enums import ChatAction, ParseMode
from pyrogram import filters
from pyrogram.types import Message

__MODULE__ = "ᴏᴘᴇɴᴀɪ"
__HELP__ = """
<b>⦪ ʙᴀɴᴛᴜᴀɴ ᴜɴᴛᴜᴋ ᴏᴘᴇɴᴀɪ ⦫</b>
<blockquote>
⎆ perintah :
ᚗ <code>{0}ai</code>
⊶ buat pertanyaan contoh <code>{0}ask</code> dimana letak Antartika</blockquote>
"""

API_KEY = os.getenv("API_KEY")

@PY.UBOT("ai")
@PY.TOP_CMD
async def chat_gpt(client, message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)

        if len(message.command) < 2:
            await message.reply_text(
                "<emoji id=5017122105011995219>⛔</emoji>mohon gunakan format\ncontoh : .ai halo"
            )
        else:
            prs = await message.reply_text(f"<emoji id=5224450179368767019>🌎</emoji>proccesing....")
            a = message.text.split(' ', 1)[1]
            url = f'https://api.botcahx.eu.org/api/search/gpt?text={a}&apikey={API_KEY}'
            response = requests.get(url)

            try:
                res_json = response.json()
                if "message" in res_json:
                    x = res_json["message"]                  
                    await prs.edit(
                      f"<blockquote>{x}</blockquote>"
                    )
                else:
                    await message.reply_text("No 'message' key found in the response.")
            except KeyError:
                await message.reply_text("Error accessing the response.")
    except Exception as e:
        await message.reply_text(f"{e}")
