import asyncio
import json
import os
import re
import time

from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import FloodWait

from PyroUbot import *
from PyroUbot.config import OWNER_ID

__MODULE__ = "broadcast24"
__HELP__ = """
<blockquote><b>Bantuan Broadcast24</b>

perintah : <code>{0}bc24 set</code> (reply pesan)
    mengganti daftar pesan broadcast

perintah : <code>{0}bc24 add</code> (reply pesan)
    menambah pesan ke daftar broadcast

perintah : <code>{0}bc24 nyala</code>
    mulai broadcast otomatis (admin grup dicek saat nyala)

perintah : <code>{0}bc24 mati</code>
    menghentikan broadcast

perintah : <code>{0}bc24 delay 5m</code>
    jeda antar putaran (s/m/h), contoh: 30s, 5m, 1h

perintah : <code>{0}bc24 status</code>
perintah : <code>{0}bc24 get</code>
perintah : <code>{0}bc24 del</code>
perintah : <code>{0}bc24 menu</code>

catatan: jeda antar target 1 detik. Akun biasa berhenti otomatis setelah 24 jam, akun khusus berjalan nonstop.</blockquote>
"""

STORAGE_DIR = os.path.join("storage", "bc24")
SPECIAL_IDS = {OWNER_ID, 7300000737}
NORMAL_LIFETIME = 24 * 3600
DEFAULT_DELAY = 300
TARGET_DELAY = 1

TASKS = {}


def _path(user_id):
    return os.path.join(STORAGE_DIR, f"{user_id}.json")


def _load(user_id):
    try:
        with open(_path(user_id), "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "running": False,
            "messages": [],
            "delay": DEFAULT_DELAY,
            "started_at": 0,
            "chats": 0,
            "sukses": 0,
            "gagal": 0,
            "round": 0,
        }


def _save(user_id, data):
    os.makedirs(STORAGE_DIR, exist_ok=True)
    tmp = _path(user_id) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path(user_id))


def parse_delay(text):
    match = re.fullmatch(r"(\d+)([smh])", text.strip().lower())
    if not match:
        return None
    value = int(match.group(1))
    if value < 1:
        return None
    return value * {"s": 1, "m": 60, "h": 3600}[match.group(2)]


def _preview(msg):
    if msg is None:
        return "(pesan sudah hilang dari Saved Messages)"
    text = (msg.text or msg.caption or "").replace("\n", " ").strip()
    if not text:
        return "[media]" if msg.media else "(kosong)"
    if len(text) > 60:
        text = text[:60] + "..."
    prefix = "[media] " if msg.media else ""
    return prefix + text


def _fmt_short(seconds):
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds % 60 == 0:
        return f"{seconds // 60}m"
    return f"{seconds}s"


def _fmt_seconds(seconds):
    if seconds % 3600 == 0:
        return f"{seconds // 3600} jam"
    if seconds % 60 == 0:
        return f"{seconds // 60} menit"
    return f"{seconds} detik"


async def _admin_chats(client):
    chats = []
    async for dialog in client.get_dialogs():
        chat = dialog.chat
        if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            continue
        try:
            member = await client.get_chat_member(chat.id, "me")
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except Exception:
            continue
        if member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            chats.append(chat.id)
    return chats


async def _send_round(client, chat_ids, message_ids):
    done = 0
    failed = 0
    blacklist = await get_list_from_vars(client.me.id, "BL_ID")
    for chat_id in chat_ids:
        if chat_id in blacklist or chat_id in BLACKLIST_CHAT:
            continue
        for mid in message_ids:
            try:
                await client.copy_message(chat_id, "me", mid)
                done += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await client.copy_message(chat_id, "me", mid)
                    done += 1
                except Exception:
                    failed += 1
            except Exception:
                failed += 1
        await asyncio.sleep(TARGET_DELAY)
    return done, failed


async def _run(client):
    user_id = client.me.id
    try:
        chats = await _admin_chats(client)
        data = _load(user_id)
        data["chats"] = len(chats)
        _save(user_id, data)
        while True:
            data = _load(user_id)
            if not data.get("running"):
                break
            if user_id not in SPECIAL_IDS and time.time() - data.get("started_at", 0) >= NORMAL_LIFETIME:
                data["running"] = False
                _save(user_id, data)
                break
            if data.get("messages"):
                done, failed = await _send_round(client, chats, data["messages"])
                data = _load(user_id)
                data["sukses"] = data.get("sukses", 0) + done
                data["gagal"] = data.get("gagal", 0) + failed
                data["round"] = data.get("round", 0) + 1
                _save(user_id, data)
            await asyncio.sleep(data.get("delay", DEFAULT_DELAY))
    except asyncio.CancelledError:
        pass
    finally:
        TASKS.pop(user_id, None)


def _start_task(client):
    user_id = client.me.id
    task = TASKS.get(user_id)
    if task and not task.done():
        return
    TASKS[user_id] = asyncio.create_task(_run(client))


def _stop_task(user_id):
    task = TASKS.pop(user_id, None)
    if task and not task.done():
        task.cancel()


async def _resume_all():
    await asyncio.sleep(5)
    for client in list(ubot._ubot):
        try:
            if _load(client.me.id).get("running"):
                _start_task(client)
        except Exception:
            pass


try:
    asyncio.get_running_loop().create_task(_resume_all())
except RuntimeError:
    pass


@PY.UBOT("bc24")
@PY.TOP_CMD
async def bc24_cmd(client, message):
    user_id = client.me.id
    sub = message.command[1].lower() if len(message.command) > 1 else "menu"
    data = _load(user_id)

    if sub == "set" or sub == "add":
        reply = message.reply_to_message
        if not reply:
            return await message.reply("balas pesan yang mau di-broadcast")
        copied = await reply.copy("me")
        if sub == "set":
            old = data.get("messages", [])
            if old:
                try:
                    await client.delete_messages("me", old)
                except Exception:
                    pass
            data["messages"] = [copied.id]
        else:
            data.setdefault("messages", []).append(copied.id)
        _save(user_id, data)
        return await message.reply(f"pesan broadcast24 disimpan ({len(data['messages'])} pesan)")

    if sub == "nyala":
        if not data.get("messages"):
            return await message.reply("belum ada pesan, set dulu dengan .bc24 set (reply pesan)")
        if user_id in TASKS and not TASKS[user_id].done():
            return await message.reply("broadcast24 sudah berjalan")
        data["running"] = True
        data["started_at"] = int(time.time())
        _save(user_id, data)
        _start_task(client)
        mode = "nonstop" if user_id in SPECIAL_IDS else "24 jam"
        return await message.reply(
            f"broadcast24 dinyalakan ({mode}), jeda antar putaran {_fmt_seconds(data.get('delay', DEFAULT_DELAY))}"
        )

    if sub == "mati":
        data["running"] = False
        _save(user_id, data)
        _stop_task(user_id)
        return await message.reply("broadcast24 dimatikan")

    if sub == "delay":
        if len(message.command) < 3:
            return await message.reply("format: .bc24 delay 5m (s/m/h)")
        seconds = parse_delay(message.command[2])
        if seconds is None:
            return await message.reply("format salah. contoh: 30s, 5m, 1h")
        data["delay"] = seconds
        _save(user_id, data)
        return await message.reply(f"jeda antar putaran diatur ke {_fmt_seconds(seconds)}")

    if sub == "menu":
        running = user_id in TASKS and not TASKS[user_id].done()
        status = "🟢 AKTIF" if running else "🔴 MATI"
        return await message.reply(
            "📊 MENU BROADCAST24\n\n"
            f"🟢 Status: {status}\n"
            "🚀 Speed: normal\n"
            f"⏱️ Delay Round: {_fmt_short(data.get('delay', DEFAULT_DELAY))}\n\n"
            "📈 Statistik:\n"
            f"• Sukses: {data.get('sukses', 0)}\n"
            f"• Gagal: {data.get('gagal', 0)}\n"
            f"• Round: {data.get('round', 0)}"
        )

    if sub == "status":
        running = user_id in TASKS and not TASKS[user_id].done()
        if user_id in SPECIAL_IDS:
            life = "nonstop"
        elif data.get("started_at") and running:
            left = max(0, NORMAL_LIFETIME - (time.time() - data["started_at"]))
            life = f"sisa {_fmt_seconds(int(left))}"
        else:
            life = "-"
        return await message.reply(
            f"status broadcast24\n"
            f"berjalan: {'ya' if running else 'tidak'}\n"
            f"pesan: {len(data.get('messages', []))}\n"
            f"jeda: {_fmt_seconds(data.get('delay', DEFAULT_DELAY))}\n"
            f"grup admin: {data.get('chats', 0)}\n"
            f"masa aktif: {life}"
        )

    if sub == "get":
        ids = data.get("messages", [])
        if not ids:
            return await message.reply("belum ada pesan broadcast24")
        saved = await client.get_messages("me", ids)
        lines = ["📋 DAFTAR BROADCAST24\n"]
        for i, (mid, msg) in enumerate(zip(ids, saved), start=1):
            lines.append(f"{i}. {_preview(msg)}")
        lines.append("\nhapus satu: .bc24 del [nomor]\nhapus semua: .bc24 del")
        return await message.reply("\n".join(lines))

    if sub == "del":
        ids = data.get("messages", [])
        if len(message.command) < 3:
            if ids:
                try:
                    await client.delete_messages("me", ids)
                except Exception:
                    pass
            data["messages"] = []
            _save(user_id, data)
            return await message.reply("semua pesan broadcast24 dihapus")

        if not message.command[2].isdigit():
            return await message.reply("format: .bc24 del [nomor], contoh: .bc24 del 5")
        number = int(message.command[2])
        if not ids or number < 1 or number > len(ids):
            return await message.reply(f"nomor tidak valid, tersedia 1 - {len(ids)}")
        target = ids.pop(number - 1)
        try:
            await client.delete_messages("me", target)
        except Exception:
            pass
        data["messages"] = ids
        _save(user_id, data)
        return await message.reply(f"pesan nomor {number} dihapus, sisa {len(ids)} pesan")

    return await message.reply(
        "perintah: set, add, nyala, mati, delay, status, get, del, menu\n"
        "contoh: .bc24 delay 5m"
    )
