"""
Anti-BT: hapus otomatis pesan admin ber-custom-title tertentu di grup terdaftar,
dilakukan bergiliran oleh semua userbot aktif. Dikontrol owner/dev.

Konfigurasi (dibaca dari env, dengan nilai default):
  ANTIBT_GROUPS  chat id grup, dipisah spasi
                 (default: -1002414865406 -1002173432931)
  ANTIBT_TITLE   custom title yang dicari, dibandingkan casefold persis
                 setelah strip (default: bt)

Pengontrol: OWNER_ID dan DEVS dari PyroUbot.config.
Penyimpanan: mongodb["antibt"], dokumen _id "settings" berisi enabled dan delay.

Perintah (prefix "/", hanya pengontrol, di private bot atau grup mana pun):
  /antibt on | off | status
  /antibt jeda 3s      format: 3s, 3, 1.5s, 500ms; rentang 0-60 detik
  /antibt@namabot ...  hanya diterima jika namabot = username bot utama

Catatan:
- Userbot yang dibuat saat runtime menerima handler setelah restart,
  sama seperti modul lain yang memakai ubot.on_message.
- Deteksi admin anonim memakai sender_chat + author_signature. Ini belum
  diverifikasi live; setiap pesan admin anonim di grup terdaftar saat fitur
  aktif dicatat ke stdout dengan nilai author_signature-nya.
"""

import asyncio
import os
import re
import time
from collections import OrderedDict
from types import SimpleNamespace

from pymongo.errors import PyMongoError
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from pyrogram.errors import FloodWait, RPCError
from pyrogram.errors.exceptions.bad_request_400 import (
    ChatAdminRequired as BadRequestChatAdminRequired,
    MessageIdInvalid,
    UserNotParticipant,
)
from pyrogram.errors.exceptions.forbidden_403 import (
    ChatAdminRequired,
    MessageDeleteForbidden,
)

from PyroUbot import bot, ubot
from PyroUbot.config import DEVS, OWNER_ID
from PyroUbot.core.database import mongodb

__MODULE__ = "ᴀɴᴛɪ-ʙᴛ"
__HELP__ = """
<b>⦪ ᴀɴᴛɪ-ʙᴛ ⦫</b>
<blockquote><b>
ᚗ <code>/antibt on</code> | <code>off</code> | <code>status</code>
ᚗ <code>/antibt jeda 3s</code>
</b></blockquote>
"""

ANTIBT_GROUPS = [
    int(x)
    for x in os.getenv("ANTIBT_GROUPS", "-1002414865406 -1002173432931").split()
]
ANTIBT_TITLE = os.getenv("ANTIBT_TITLE", "bt").strip()
CONTROLLERS = {OWNER_ID, *DEVS}

WATCH_GROUP = 76
CMD_GROUP = 77
ADMIN_CACHE_TTL = 120
ELIGIBLE_TTL = 600
PENALTY_TTL = 600
MAX_FLOOD_WAIT = 5
DEFAULT_DELAY = 3.0
MAX_DELAY = 60.0
CLAIM_CAP = 2000
CLAIM_TTL = 120

COLLECTION = mongodb["antibt"]
SETTINGS_ID = "settings"
DEFAULTS = {"enabled": False, "delay": DEFAULT_DELAY}

CMD_PATTERN = r"^/antibt(?:@(\w+))?(?:\s+(.*?))?\s*$"
CMD_RE = re.compile(CMD_PATTERN, re.IGNORECASE | re.DOTALL)
CMD_FILTER = filters.regex(CMD_PATTERN, flags=re.IGNORECASE | re.DOTALL)
DELAY_RE = re.compile(r"^(\d+(?:\.\d+)?)(s|ms)?$", re.IGNORECASE)

USAGE = "Format: /antibt on | off | status | jeda <waktu>"
USAGE_JEDA = (
    "❌ Format jeda salah atau di luar rentang 0-60 detik.\n"
    "Contoh: /antibt jeda 3s, /antibt jeda 1.5s, /antibt jeda 500ms"
)

_now = time.monotonic


def _log(msg):
    print(f"[ANTIBT] {msg}")


class Claimer:
    """Memastikan satu key hanya diproses sekali (TTL dan batas jumlah entri)."""

    def __init__(self, cap=CLAIM_CAP, ttl=CLAIM_TTL):
        self._items = OrderedDict()
        self._cap = cap
        self._ttl = ttl

    def claim(self, key):
        now = _now()
        while self._items:
            _, ts = next(iter(self._items.items()))
            if now - ts < self._ttl:
                break
            self._items.popitem(last=False)
        if key in self._items:
            return False
        self._items[key] = now
        while len(self._items) > self._cap:
            self._items.popitem(last=False)
        return True


class _State:
    def __init__(self):
        self.settings = None  # dict, dimuat dari Mongo sekali
        self.last_uid = 0  # kursor giliran global
        self.deleted = 0
        self.admin_cache = {}  # chat_id -> (ts, {user_id: custom_title})
        self.admin_locks = {}
        self.elig = {}  # (client_id, chat_id) -> (expires, bool)
        self.penalty = {}  # (client_id, chat_id) -> until
        self.tasks = set()


state = _State()
claimer = Claimer()  # pesan target dan command
anon_log = Claimer()  # hanya untuk log admin anonim


# ---------------------------------------------------------------- pengaturan


async def _ensure_loaded():
    if state.settings is None:
        doc = await COLLECTION.find_one({"_id": SETTINGS_ID})  # PyMongoError diteruskan
        loaded = dict(DEFAULTS)
        if doc:
            loaded.update({k: doc[k] for k in DEFAULTS if k in doc})
        state.settings = loaded
    return state.settings


async def get_settings():
    try:
        return await _ensure_loaded()
    except PyMongoError as e:
        _log(f"gagal memuat pengaturan: {e}")
        return dict(DEFAULTS)  # tidak di-cache, jadi aman (fitur dianggap off)


async def save_settings(**fields):
    settings = await _ensure_loaded()
    await COLLECTION.update_one(
        {"_id": SETTINGS_ID}, {"$set": fields}, upsert=True
    )
    settings.update(fields)


# ---------------------------------------------------------------- util


def title_matches(title):
    return isinstance(title, str) and title.strip().casefold() == ANTIBT_TITLE.casefold()


def parse_delay(text):
    """Mengembalikan detik (float) atau None jika format/rentang salah."""
    m = DELAY_RE.match((text or "").strip())
    if not m:
        return None
    value = float(m.group(1))
    if (m.group(2) or "s").lower() == "ms":
        value /= 1000
    if 0 <= value <= MAX_DELAY:
        return value
    return None


def _fmt_delay(value):
    return f"{value:g}"


def pick_next(candidate_ids, last):
    """Id terkecil yang lebih besar dari last; jika tidak ada, kembali ke id terkecil."""
    ids = sorted(candidate_ids)
    if not ids:
        return None
    for uid in ids:
        if uid > last:
            return uid
    return ids[0]


def _client_by_id(uid):
    for c in ubot._ubot:
        if c.me and c.me.id == uid:
            return c
    return None


# ---------------------------------------------------------------- admin & eligibility


async def get_admin_titles(client, chat_id):
    entry = state.admin_cache.get(chat_id)
    if entry and _now() - entry[0] < ADMIN_CACHE_TTL:
        return entry[1]
    lock = state.admin_locks.setdefault(chat_id, asyncio.Lock())
    async with lock:
        entry = state.admin_cache.get(chat_id)
        if entry and _now() - entry[0] < ADMIN_CACHE_TTL:
            return entry[1]
        titles = {}
        try:
            async for member in client.get_chat_members(
                chat_id, filter=ChatMembersFilter.ADMINISTRATORS
            ):
                if member.user:
                    titles[member.user.id] = member.custom_title or ""
        except RPCError as e:
            _log(f"gagal memuat admin {chat_id}: {e}")
            return entry[1] if entry else {}
        state.admin_cache[chat_id] = (_now(), titles)
        return titles


async def is_target(client, message):
    chat_id = message.chat.id
    if message.sender_chat is not None:
        if message.sender_chat.id != chat_id:
            return False
        signature = message.author_signature
        if anon_log.claim(("anon", chat_id, message.id)):
            _log(
                f"admin anonim chat={chat_id} msg={message.id} "
                f"author_signature={signature!r}"
            )
        return title_matches(signature)
    user = message.from_user
    if user is None:
        return False
    titles = await get_admin_titles(client, chat_id)
    return user.id in titles and title_matches(titles[user.id])


async def is_eligible(client, chat_id, force=False):
    key = (client.me.id, chat_id)
    now = _now()
    if state.penalty.get(key, 0) > now:
        return False
    if not force:
        cached = state.elig.get(key)
        if cached and cached[0] > now:
            return cached[1]
    try:
        member = await client.get_chat_member(chat_id, "me")
    except UserNotParticipant:
        state.elig[key] = (now + ELIGIBLE_TTL, False)
        return False
    except RPCError as e:
        _log(f"cek eligibility {client.me.id}@{chat_id} gagal: {e}")
        return False
    ok = member.status == ChatMemberStatus.OWNER or (
        member.status == ChatMemberStatus.ADMINISTRATOR
        and bool(member.privileges and member.privileges.can_delete_messages)
    )
    state.elig[key] = (now + ELIGIBLE_TTL, ok)
    return ok


async def eligible_clients(chat_id, force=False):
    """Userbot aktif saat ini yang eligible di chat_id, diurutkan berdasarkan user id."""
    clients = list(ubot._ubot)
    results = await asyncio.gather(
        *(is_eligible(c, chat_id, force) for c in clients)
    )
    return sorted(
        (c for c, ok in zip(clients, results) if ok), key=lambda c: c.me.id
    )


def _penalize(uid, chat_id):
    state.penalty[(uid, chat_id)] = _now() + PENALTY_TTL


# ---------------------------------------------------------------- penghapusan


async def _try_delete(client, chat_id, msg_id, uid):
    """Mengembalikan 'ok', 'gone', 'retry' (oper ke userbot lain) atau 'stop'."""
    try:
        await client.delete_messages(chat_id, msg_id)
        return "ok"
    except MessageIdInvalid:
        return "gone"
    except FloodWait as e:
        wait = min(e.value or 0, MAX_FLOOD_WAIT)
        _log(f"FloodWait {e.value}s pada {uid}@{chat_id}, tunggu {wait}s lalu oper")
        _penalize(uid, chat_id)
        await asyncio.sleep(wait)
        return "retry"
    except (MessageDeleteForbidden, ChatAdminRequired, BadRequestChatAdminRequired):
        _log(f"{uid} tidak bisa menghapus di {chat_id}, oper ke userbot lain")
        _penalize(uid, chat_id)
        return "retry"
    except RPCError as e:
        _log(f"hapus msg {msg_id} di {chat_id} oleh {uid} gagal: {e}")
        return "stop"


async def _delete_with_handover(chat_id, msg_id, uid):
    tried = set()
    while uid is not None:
        tried.add(uid)
        client = _client_by_id(uid)
        if client is None:
            outcome = "retry"
        else:
            outcome = await _try_delete(client, chat_id, msg_id, uid)
        if outcome == "ok":
            state.deleted += 1
            return
        if outcome in ("gone", "stop"):
            return
        candidates = [
            c.me.id for c in await eligible_clients(chat_id) if c.me.id not in tried
        ]
        uid = pick_next(candidates, last=uid)
        if uid is not None:
            state.last_uid = uid
    _log(f"semua userbot gagal menghapus msg {msg_id} di {chat_id}")


async def _run_delete(chat_id, msg_id, uid, delay):
    await asyncio.sleep(delay)
    settings = await get_settings()
    if not settings["enabled"]:
        return
    await _delete_with_handover(chat_id, msg_id, uid)


def _schedule(chat_id, msg_id, uid, delay):
    task = asyncio.create_task(_run_delete(chat_id, msg_id, uid, delay))
    state.tasks.add(task)
    task.add_done_callback(state.tasks.discard)


def _cancel_tasks():
    pending = [t for t in state.tasks if not t.done()]
    for t in pending:
        t.cancel()
    return len(pending)


# ---------------------------------------------------------------- watcher pesan


async def _watch(client, message):
    chat_id = message.chat.id
    if chat_id not in ANTIBT_GROUPS:
        return
    if message.service:
        return
    settings = await get_settings()
    if not settings["enabled"]:
        return
    if not await is_target(client, message):
        return
    if not claimer.claim(("msg", chat_id, message.id)):
        return
    eligible = await eligible_clients(chat_id)
    uid = pick_next([c.me.id for c in eligible], state.last_uid)
    if uid is None:
        _log(f"tidak ada userbot eligible di {chat_id}, msg {message.id} dilewati")
        return
    state.last_uid = uid
    _schedule(chat_id, message.id, uid, settings["delay"])


@ubot.on_message(filters.group, group=WATCH_GROUP)
async def antibt_watch(client, message):
    try:
        await _watch(client, message)
    except Exception as e:  # jaring pengaman: handler tidak boleh jatuh
        _log(f"error pada watcher: {e!r}")


# ---------------------------------------------------------------- command


async def _status_text():
    settings = await get_settings()
    lines = [
        "🛡️ Anti-BT",
        f"Status: {'aktif' if settings['enabled'] else 'nonaktif'}",
        f"Jeda: {_fmt_delay(settings['delay'])} detik",
        f"Title: {ANTIBT_TITLE}",
        "Grup:",
    ]
    for chat_id in ANTIBT_GROUPS:
        count = len(await eligible_clients(chat_id, force=True))
        lines.append(f"- {chat_id}: {count} userbot eligible")
    lines.append(f"Terhapus sejak bot hidup: {state.deleted}")
    return "\n".join(lines)


async def _run_command(args):
    parts = args.split(None, 1)
    sub = parts[0].casefold() if parts else "status"
    rest = parts[1] if len(parts) > 1 else ""
    try:
        if sub in ("", "status"):
            return await _status_text()
        if sub == "on":
            await save_settings(enabled=True)
            return "✅ Anti-BT aktif"
        if sub == "off":
            pending = len(state.tasks)
            await save_settings(enabled=False)
            _cancel_tasks()
            return f"⛔ Anti-BT nonaktif ({pending} penghapusan tertunda dibatalkan)"
        if sub == "jeda":
            delay = parse_delay(rest)
            if delay is None:
                return USAGE_JEDA
            await save_settings(delay=delay)
            return f"⏱️ Jeda diatur ke {_fmt_delay(delay)} detik"
    except PyMongoError as e:
        _log(f"gagal menyimpan pengaturan: {e}")
        return "❌ Gagal menyimpan pengaturan ke database"
    return USAGE


async def _command(client, message):
    user = message.from_user
    if user is None or user.id not in CONTROLLERS:
        return
    m = CMD_RE.match(message.text or "")
    if not m:
        return
    mention, args = m.group(1), (m.group(2) or "").strip()
    if mention is not None:
        my_name = bot.me.username if bot.me else None
        if not my_name or mention.casefold() != my_name.casefold():
            return
    if not claimer.claim(("cmd", message.chat.id, message.id)):
        return
    reply = await _run_command(args)
    await message.reply_text(reply, quote=True)


@ubot.on_message(CMD_FILTER, group=CMD_GROUP)
@bot.on_message(CMD_FILTER, group=CMD_GROUP)
async def antibt_command(client, message):
    try:
        await _command(client, message)
    except RPCError as e:
        _log(f"balasan command gagal: {e}")
    except Exception as e:  # jaring pengaman: handler tidak boleh jatuh
        _log(f"error pada command: {e!r}")
