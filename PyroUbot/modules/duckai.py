from PyroUbot import *
import random
import requests
from pyrogram.enums import ChatAction, ParseMode
from pyrogram import filters
from pyrogram.types import Message

__MODULE__ = "ᴅᴜᴄᴋ ᴀɪ"
__HELP__ = """
<b>⦪ ʙᴀɴᴛᴜᴀɴ ᴜɴᴛᴜᴋ ᴅᴜᴄᴋ ᴀɪ ⦫</b>
<blockquote>
⎆ perintah :
ᚗ <code>{0}duckai</code>
⊶ Ai yang bisa memberikan tips dan saran.
</blockquote>
"""


@PY.UBOT("duckai")
@PY.TOP_CMD
async def chat_gpt(client, message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)

        if len(message.command) < 2:
            await message.reply_text(
                "<emoji id=5019523782004441717>❌</emoji>mohon gunakan format\ncontoh : .duckai query"
            )
        else:
            prs = await message.reply_text(f"<emoji id=5319230516929502602>🔍</emoji>menjawab....")
            a = message.text.split(' ', 1)[1]
            respons = requests.get(f'https://api.siputzx.my.id/api/ai/duckai?query={a}')

            try:
                if "response" in respons.json():
                    x = respons.json()["response"]                  
                    await prs.edit(
                      f"<blockquote>{x}</blockquote>"
                    )
                else:
                    await message.reply_text("No 'results' key found in the response.")
            except KeyError:
                await message.reply_text("Error accessing the response.")
    except Exception as e:
        await message.reply_text(f"{e}")
