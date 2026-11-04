from PyroUbot import *
import random
import requests
from pyrogram.enums import ChatAction, ParseMode
from pyrogram import filters
from pyrogram.types import Message

__MODULE__ = "sʜᴏʀᴛ ʟɪɴᴋ"
__HELP__ = """
<b>⦪ ʙᴀɴᴛᴜᴀɴ ᴜɴᴛᴜᴋ sʜᴏʀᴛ ʟɪɴᴋ ⦫</b>
<blockquote>⎆ perintah :
ᚗ <code>{0}tinyurl</code> link
⊶ dapat memperpendek tautan url yang panjang

ᚗ <code>{0}bitly</code> link
⊶ dapat memperpendek tautan url yang panjang</blockquote>
"""


@PY.UBOT("tinyurl")
@PY.TOP_CMD
async def chat_gpt(client, message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)

        if len(message.command) < 2:
            await message.reply_text(
                "<emoji id=5019523782004441717>❌</emoji>mohon gunakan format\ncontoh : .tinyurl https://google.com"
            )
        else:
            prs = await message.reply_text(f"<emoji id=5071138963800982678>😎</emoji> Proses....")
            a = message.text.split(' ', 1)[1]
            response = requests.get(f'https://api.botcahx.eu.org/api/linkshort/tinyurl?link={a}&apikey=_@moire_mor')

            try:
                if "result" in response.json():
                    x = response.json()["result"]                  
                    await prs.edit(
                      f"{x}"
                    )
                else:
                    await message.reply_text("No 'results' key found in the response.")
            except KeyError:
                await message.reply_text("Error accessing the response.")
    except Exception as e:
        await message.reply_text(f"{e}")


@PY.UBOT("bitly")
@PY.TOP_CMD
async def chat_gpt(client, message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)

        if len(message.command) < 2:
            await message.reply_text(
                "<emoji id=5019523782004441717>❌</emoji>mohon gunakan format\ncontoh : .bitly https://google.com"
            )
        else:
            prs = await message.reply_text(f"<emoji id=5071138963800982678>😎</emoji> Proses....")
            a = message.text.split(' ', 1)[1]
            response = requests.get(f'https://api.botcahx.eu.org/api/linkshort/bitly?link={a}&apikey=_@moire_mor')

            try:
                if "result" in response.json():
                    x = response.json()["result"]                  
                    await prs.edit(
                      f"{x}"
                    )
                else:
                    await message.reply_text("No 'results' key found in the response.")
            except KeyError:
                await message.reply_text("Error accessing the response.")
    except Exception as e:
        await message.reply_text(f"{e}")
        
