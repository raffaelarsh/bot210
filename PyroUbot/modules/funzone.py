from pyrogram import Client
import requests
import os
import random

from PyroUbot import *

__MODULE__ = "ғᴜɴᴢᴏɴᴇ"

__HELP__ = """
<blockquote><code>{0}rate</code> <teks>
→ Menilai sesuatu secara random

<code>{0}ship</code>
→ Cocokkan kamu dengan member random

<code>{0}truth</code>
→ Pertanyaan jujur

<code>{0}dare</code>
→ Tantangan random

<code>{0}roast</code>
→ Roast ringan & aman

<code>{0}persona</code>
→ Generate kepribadian kamu

<code>{0}scenario</code>
→ Skenario random absurd

<code>{0}npc</code>
→ Jawaban ala NPC game

<code>{0}emojify</code> <teks>
→ Tambahin emoji random ke teks</blockquote>
"""

# ================= DATA ================= #

TRUTH = [
    "Apa rahasia yang belum pernah kamu ceritakan?",
    "Siapa orang terakhir yang kamu stalk?",
    "Hal paling memalukan dalam hidupmu?",
]

DARE = [
    "Kirim emoji random sekarang!",
    "Tag orang terakhir yang chat kamu",
    "Ketik 'aku ganteng' tanpa hapus",
]

ROAST = [
    "Kamu bukan jelek, cuma kurang update 😌",
    "Otakmu loading tapi sinyalnya E",
    "Kamu unik, sayang cuma di pikiranmu",
]

PERSONA = [
    "Ambisius • Alpha • Visioner",
    "Santai • Observer • Netral",
    "Dominan • Strategist • Leader",
    "Chaos • Kreatif • Rebel",
]

SCENARIO = [
    "Kamu ketemu mantan jam 3 pagi di Indomaret.",
    "Tiba-tiba kamu jadi admin grup isinya mantan semua.",
    "Bangun tidur, kamu jadi bot Telegram.",
]

NPC = [
    "Selamat datang, petualang.",
    "Aku tidak punya quest untukmu.",
    "Kembali lagi nanti.",
]

EMOJIS = ["🔥", "😂", "💀", "😎", "✨", "👀", "💎", "🗿"]

# ================= COMMANDS ================= #

@PY.UBOT("rate")
async def rate_cmd(client: Client, message):
    teks = message.text.split(None, 1)
    if len(teks) < 2:
        return await message.reply("Kasih teks yang mau dinilai.")
    nilai = round(random.uniform(1, 10), 1)
    await message.reply(f"📊 Rating **{teks[1]}**: **{nilai}/10**")

@PY.UBOT("ship")
async def ship_cmd(client: Client, message):
    members = [m async for m in client.get_chat_members(message.chat.id, limit=20)]
    if len(members) < 2:
        return await message.reply("Kurang member.")
    a, b = random.sample(members, 2)
    persen = random.randint(40, 100)
    await message.reply(
        f"💘 **SHIP RESULT**\n"
        f"{a.user.first_name} ❤️ {b.user.first_name}\n"
        f"Kecocokan: **{persen}%**"
    )

@PY.UBOT("truth")
async def truth_cmd(client: Client, message):
    await message.reply("🧠 **TRUTH:**\n" + random.choice(TRUTH))

@PY.UBOT("dare")
async def dare_cmd(client: Client, message):
    await message.reply("🔥 **DARE:**\n" + random.choice(DARE))

@PY.UBOT("roast")
async def roast_cmd(client: Client, message):
    await message.reply("☕ " + random.choice(ROAST))

@PY.UBOT("persona")
async def persona_cmd(client: Client, message):
    await message.reply(
        "🧬 **PERSONA KAMU:**\n" + random.choice(PERSONA)
    )

@PY.UBOT("scenario")
async def scenario_cmd(client: Client, message):
    await message.reply(
        "🎬 **SCENARIO:**\n" + random.choice(SCENARIO)
    )

@PY.UBOT("npc")
async def npc_cmd(client: Client, message):
    await message.reply(
        "🧍 **NPC:**\n" + random.choice(NPC)
    )

@PY.UBOT("emojify")
async def emojify_cmd(client: Client, message):
    teks = message.text.split(None, 1)
    if len(teks) < 2:
        return await message.reply("Kasih teks.")
    hasil = ""
    for c in teks[1]:
        hasil += c + random.choice(EMOJIS)
    await message.reply(hasil)