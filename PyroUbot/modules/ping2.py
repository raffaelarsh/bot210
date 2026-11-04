import os
import json
import asyncio
import psutil
# import speedtest
from speedtest import Speedtest
import random

from datetime import datetime
from gc import get_objects
from time import time

from pyrogram.raw import *
from pyrogram.raw.functions import Ping
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from PyroUbot import *

__MODULE__ = "ᴘɪɴɢ"
__HELP__ = """
<b>⦪ ʙᴀɴᴛᴜᴀɴ ᴜɴᴛᴜᴋ ᴘɪɴɢ ⦫</b>

<blockquote>⎆ perintah :
ᚗ <code>{0}ping</code>

ᚗ <code>{0}ping1</code>

ᚗ <code>{0}ping2</code></blockquote>

"""
class speed:
    SpeedTest = (
        "Speedtest started at `{start}`\n"
        "Ping ➠ `{ping}` ms\n"
        "Download ➠ `{download}`\n"
        "Upload ➠ `{upload}`\n"
        "ISP ➠ __{isp}__"
    )

    NearestDC = "Country: `{}`\n" "Nearest Datacenter: `{}`\n" "This Datacenter: `{}`"

async def _(client, message):
    start = datetime.now()
    await client.invoke(Ping(ping_id=0))
    end = datetime.now()
    uptime = await get_time((time() - start_time))
    delta_ping_formatted = round((end - start).microseconds / 10000, 2)
    pong = await EMO.PING(client)
    tion = await EMO.MENTION(client)
    yubot = await EMO.UBOT(client)
    pantek = await STR.PONG(client)
    ngentod = await STR.OWNER(client)
    kontol = await STR.UBOT(client)
    devs = await STR.DEVS(client)
    babi = client.me.is_premium
    if babi:
        _ping = f"""
<blockquote>{pong} {pantek} : {str(delta_ping_formatted).replace('.', ',')} ms
{tion} {ngentod} : <code>{client.me.mention}</code>
{yubot} {kontol} : <code>{bot.me.mention}</code></blockquote>

<blockquote><b>ᣃ࿈ ᴜsᴇʀʙᴏᴛ ᴘʀᴇᴍɪᴜᴍ ࿈ᣄ</b></blockquote>"""
        await message.reply(_ping)
    else:
        _ping = f"""
<blockquote>{pantek} : {str(delta_ping_formatted).replace('.', ',')} ms
{ngentod} : <code>{client.me.mention}</code>
{kontol} : <code>{bot.me.mention}</code></blockquote>

<blockquote><b>ᣃ࿈ ᴜsᴇʀʙᴏᴛ ᴘʀᴇᴍɪᴜᴍ ࿈ᣄ</b></blockquote>"""
        await message.reply(_ping)

@PY.UBOT("ping1")
@PY.TOP_CMD
async def _(client, message):
    start = datetime.now()
    await client.invoke(Ping(ping_id=0))
    end = datetime.now()
    uptime = await get_time((time() - start_time))
    delta_ping_formatted = round((end - start).microseconds / 10000, 2)
    pong = await EMO.PING(client)
    tion = await EMO.MENTION(client)
    yubot = await EMO.UBOT(client)
    pantek = await STR.PONG(client)
    ngentod = await STR.OWNER(client)
    kontol = await STR.UBOT(client)
    devs = await STR.DEVS(client)  
    xx = await message.edit("𖣐")
    await asyncio.sleep(0.3)
    await xx.edit("𖣐𖣐")
    await asyncio.sleep(0.3)
    await xx.edit("𖣐𖣐𖣐")
    await asyncio.sleep(0.3)
    await xx.edit("𖣐𖣐𖣐𖣐")
    await asyncio.sleep(0.3)
    await xx.edit("𖣐𖣐𖣐𖣐𖣐")
    await asyncio.sleep(0.3)
    await xx.edit("⚡")
    await asyncio.sleep(0.5)
    babi = client.me.is_premium
    if babi:
        _ping = f"""
<blockquote>⎆ <emoji id=5260547274957672345>🎲</emoji> ᴘɪɴɢ : {str(delta_ping_formatted).replace('.', ',')} ms
⎆ <emoji id=5235948055928262102>⭐</emoji> ᴜᴘᴛɪᴍᴇ : {uptime}
⎆ <emoji id=5204015897500469606>😢</emoji> ᴋɪɴɢ : <code>{client.me.mention}</code>
⎆ <emoji id=5194979342144260681>😂</emoji> ᴡᴀʀʀɪᴏʀ : <code>{bot.me.mention}</code></blockquote>

<blockquote><b><emoji id=6142927453854632687>🚬</emoji> ᣃ࿈ ᴜsᴇʀʙᴏᴛ ᴘʀᴇᴍɪᴜᴍ ࿈ᣄ <emoji id=6142927453854632687>🚬</emoji></b></blockquote>"""
        await message.reply(_ping)
    else:
        _ping = f"""
<blockquote>⎆ <emoji id=5260547274957672345>🎲</emoji> ᴘɪɴɢ : {str(delta_ping_formatted).replace('.', ',')} ms
⎆ <emoji id=5235948055928262102>⭐</emoji> ᴜᴘᴛɪᴍᴇ : {uptime}
⎆ <emoji id=5204015897500469606>😢</emoji> ᴋɪɴɢ : <code>{client.me.mention}</code>
⎆ <emoji id=5194979342144260681>😂</emoji> ᴡᴀʀʀɪᴏʀ : <code>{bot.me.mention}</code></blockquote>

<blockquote><b><emoji id=6142927453854632687>🚬</emoji> ᣃ࿈ ᴜsᴇʀʙᴏᴛ ᴘʀᴇᴍɪᴜᴍ ࿈ᣄ <emoji id=6142927453854632687>🚬</emoji></b></blockquote>"""
        await message.reply(_ping)

@PY.UBOT("ping2")
@PY.TOP_CMD
async def _(client, message):
    start = datetime.now()
    await client.invoke(Ping(ping_id=0))
    end = datetime.now()
    uptime = await get_time((time() - start_time))
    delta_ping_formatted = round((end - start).microseconds / 10000, 2)
    pong = await EMO.PING(client)
    tion = await EMO.MENTION(client)
    yubot = await EMO.UBOT(client)
    pantek = await STR.PONG(client)
    ngentod = await STR.OWNER(client)
    kontol = await STR.UBOT(client)
    devs = await STR.DEVS(client)  
    xx = await message.edit("★ PING ★")
    await asyncio.sleep(0.5)
    await xx.edit("★★ PING ★★")
    await asyncio.sleep(0.5)
    await xx.edit("★★★ PING ★★★")
    await asyncio.sleep(0.5)
    await xx.edit("★★★★ PING ★★★★")
    await asyncio.sleep(0.5)
    await xx.edit("✦҈͜͡➳ PONG!")
    await asyncio.sleep(0.5)
    await xx.edit("🌩")
    await asyncio.sleep(0.5)
    babi = client.me.is_premium
    if babi:
        _ping = f"""
<blockquote><emoji id=5897929355216034070>🤩</emoji> ❃ **Ping !!**
{str(delta_ping_formatted).replace('.', ',')} ms

<emoji id=5900041834880571364>😈</emoji> ❃ **Uptime -**
{uptime}

<emoji id=5897741587835786345>🔥</emoji> **✦҈͜͡➳ Master :**
<code>{client.me.mention}</code>

<emoji id=5900145373657176313>😂</emoji> **✦҈͜͡➳ Bot :**
<code>{bot.me.mention}</code></blockquote>

<blockquote><b><emoji id=6142927453854632687>🚬</emoji> ᣃ࿈ ᴜsᴇʀʙᴏᴛ ᴘʀᴇᴍɪᴜᴍ ࿈ᣄ <emoji id=6142927453854632687>🚬</emoji></b></blockquote>"""
        await message.reply(_ping)
    else:
        _ping = f"""
<blockquote><emoji id=5897929355216034070>🤩</emoji> ❃ **Ping !!**
{str(delta_ping_formatted).replace('.', ',')} ms

<emoji id=5900041834880571364>😈</emoji> ❃ **Uptime -**
{uptime}

<emoji id=5897741587835786345>🔥</emoji> **✦҈͜͡➳ Master :**
<code>{client.me.mention}</code>

<emoji id=5900145373657176313>😂</emoji> **✦҈͜͡➳ Bot :**
<code>{bot.me.mention}</code></blockquote>

<blockquote><b><emoji id=6142927453854632687>🚬</emoji> ᣃ࿈ ᴜsᴇʀʙᴏᴛ ᴘʀᴇᴍɪᴜᴍ ࿈ᣄ <emoji id=6142927453854632687>🚬</emoji></b></blockquote>"""
        await message.reply(_ping)

@PY.UBOT("p")
@PY.TOP_CMD
async def _(client, message):
    start = datetime.now()
    await client.invoke(Ping(ping_id=0))
    end = datetime.now()
    uptime = await get_time((time() - start_time))
    delta_ping_formatted = round((end - start).microseconds / 10000, 2)
    pong = await EMO.PING(client)
    tion = await EMO.MENTION(client)
    yubot = await EMO.UBOT(client)
    pantek = await STR.PONG(client)
    ngentod = await STR.OWNER(client)
    kontol = await STR.UBOT(client)
    devs = await STR.DEVS(client)  
    xx = await message.edit("▩▩▩▩▩<emoji id=6332421827565982132>😎</emoji>")
    await asyncio.sleep(0.3)
    await xx.edit("▩▩▩▩■<emoji id=6332421827565982132>😎</emoji>")
    await asyncio.sleep(0.3)
    await xx.edit("▩▩▩■■<emoji id=6332421827565982132>😎</emoji>")
    await asyncio.sleep(0.3)
    await xx.edit("▩▩■■■<emoji id=6332421827565982132>😎</emoji>")
    await asyncio.sleep(0.3)
    await xx.edit("▩■■■■<emoji id=6332421827565982132>😎</emoji>")
    await asyncio.sleep(0.3)
    await xx.edit("■■■■■<emoji id=6332421827565982132>😎</emoji>")
    await asyncio.sleep(0.3)
    await xx.edit("<emoji id=6332421827565982132>😎</emoji>")
    await asyncio.sleep(0.5)
    babi = client.me.is_premium
    if babi:
        _ping = f"""
<emoji id=5334738840676475461>😎</emoji> ᴘɪɴɢ : {str(delta_ping_formatted).replace('.', ',')} ms
⎆ <emoji id=6332068553620982747>😎</emoji> ᴜᴘᴛɪᴍᴇ : {uptime}
⎆ <emoji id=5420328446439992370>😎</emoji> ᴋɪɴɢ : <code>{client.me.mention}</code>
⎆ <emoji id=5352784961814405440>😎</emoji> ᴡᴀʀʀɪᴏʀ : <code>{bot.me.mention}</code></blockquote>

<blockquote><b><emoji id=5400297831367979161>🗡</emoji> ᣃ࿈ ᴜsᴇʀʙᴏᴛ ᴘʀᴇᴍɪᴜᴍ ࿈ᣄ <emoji id=5400297831367979161>🗡</emoji></b></blockquote>"""
        await message.reply(_ping)
    else:
        _ping = f"""
<blockquote>⎆ <emoji id=6332421827565982132>😎</emoji> ᴘɪɴɢ : {str(delta_ping_formatted).replace('.', ',')} ms
⎆ <emoji id=5080277662069425163>😎</emoji> ᴜᴘᴛɪᴍᴇ : {uptime}
⎆ <emoji id=5080240441882838117>😎</emoji> ᴋɪɴɢ : <code>{client.me.mention}</code>
⎆ <emoji id=5071138963800982678>😎</emoji> ᴡᴀʀʀɪᴏʀ : <code>{bot.me.mention}</code></blockquote>

<blockquote><b><emoji id=5400297831367979161>🗡</emoji> ᣃ࿈ ᴜsᴇʀʙᴏᴛ ᴘʀᴇᴍɪᴜᴍ ࿈ᣄ <emoji id=5400297831367979161>🗡</emoji></b></blockquote>"""
        await message.reply(_ping)
