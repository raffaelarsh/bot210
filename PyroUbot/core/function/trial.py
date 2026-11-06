"""Coba trial: verifikasi join grup, autobroadcast, dan logout otomatis saat habis."""

import asyncio
from datetime import datetime, timedelta, timezone as dt_timezone

import pytz
from pymongo.errors import DuplicateKeyError
from pyrogram.errors import FloodWait, RPCError, UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from PyroUbot import bot, ubot
from PyroUbot.config import GROUP_TRIAL_IDS, TRIAL_BROADCAST_HOURS, TRIAL_DAYS
from PyroUbot.core.database import mongodb
from PyroUbot.core.database.expired import (
    get_expired_date,
    rem_expired_date,
    set_expired_date,
)
from PyroUbot.core.database.userbot import remove_ubot
from PyroUbot.core.database.variabel import (
    add_to_vars,
    get_list_from_vars,
    remove_all_vars,
    remove_from_vars,
)

__all__ = [
    "TRIAL_BROADCAST_TEXT",
    "TrialError",
    "TrialGroupError",
    "trial_status",
    "trial_is_active",
    "trial_missing_groups",
    "trial_activate",
    "trial_is_paid_premium",
    "trial_scheduler",
]

TRIALS = mongodb["trial_users"]
PAID_TRX = mongodb["autogopay_trx"]
JAKARTA = pytz.timezone("Asia/Jakarta")
MEMBER_STATUSES = {"MEMBER", "ADMINISTRATOR", "OWNER", "CREATOR"}

TRIAL_BROADCAST_TEXT = """CAPEK /SHARE SHARE MANUAL?

TENANG ADA USER BOT SENNA
FREE TRIAL 5 DAYS
@privateubotsennabot

@privateubotsennabot

@privateubotsennabot"""

_locks: dict = {}


class TrialError(Exception):
    """Pesan aman untuk user."""


class TrialGroupError(Exception):
    """Bot tidak bisa memeriksa keanggotaan grup (bukan admin / grup salah)."""

    def __init__(self, chat_id, reason: str):
        super().__init__(f"{chat_id}: {reason}")
        self.chat_id = chat_id
        self.reason = reason


def _utcnow() -> datetime:
    return datetime.now(dt_timezone.utc).replace(tzinfo=None)


def _to_utc_naive(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(dt_timezone.utc).replace(tzinfo=None)


def _to_jakarta(dt):
    return pytz.utc.localize(_to_utc_naive(dt)).astimezone(JAKARTA)


def _lock(user_id: int) -> asyncio.Lock:
    return _locks.setdefault(user_id, asyncio.Lock())


async def trial_status(user_id: int):
    """Mengembalikan (status, doc): status 'active' | 'expired' | None."""
    doc = await TRIALS.find_one({"user_id": user_id})
    if not doc:
        return None, None
    return doc.get("status"), doc


async def trial_is_active(user_id: int) -> bool:
    status, _ = await trial_status(user_id)
    return status == "active"


async def trial_is_paid_premium(user_id: int) -> bool:
    """True jika user premium yang BUKAN dari trial (berbayar / diberikan owner).

    Saat trial berakhir tanpa pembayaran, _end_trial mencabut user dari PREM_USERS.
    Jadi user yang masih ada di PREM_USERS dan trial-nya bukan 'active' sudah berbayar.
    """
    in_list = user_id in await get_list_from_vars(bot.me.id, "PREM_USERS")
    status, _ = await trial_status(user_id)
    return in_list and status != "active"


async def trial_missing_groups(user_id: int) -> list:
    """Daftar nomor grup (1-based) yang belum di-join user."""
    if not GROUP_TRIAL_IDS:
        raise TrialGroupError(None, "GROUP_TRIAL_IDS belum diisi")
    missing = []
    for idx, chat_id in enumerate(GROUP_TRIAL_IDS, start=1):
        try:
            member = await bot.get_chat_member(chat_id, user_id)
        except UserNotParticipant:
            missing.append(idx)
            continue
        except RPCError as e:
            raise TrialGroupError(chat_id, str(e))
        status = getattr(member.status, "name", str(member.status)).upper()
        if status not in MEMBER_STATUSES:
            missing.append(idx)
    return missing


async def trial_activate(user_id: int) -> dict:
    """Aktifkan trial TRIAL_DAYS hari. Hanya sekali per user_id."""
    async with _lock(user_id):
        status, _ = await trial_status(user_id)
        if status is not None:
            raise TrialError("Trial sudah pernah digunakan untuk akun ini.")
        now = _utcnow()
        expires = now + timedelta(days=TRIAL_DAYS)
        doc = {
            "user_id": user_id,
            "status": "active",
            "joined_at": now,
            "trial_started_at": now,
            "trial_expires_at": expires,
            "last_broadcast_at": None,
        }
        try:
            res = await TRIALS.update_one(
                {"user_id": user_id}, {"$setOnInsert": doc}, upsert=True
            )
        except DuplicateKeyError:
            raise TrialError("Trial sudah pernah digunakan untuk akun ini.")
        if res.upserted_id is None:
            raise TrialError("Trial sudah pernah digunakan untuk akun ini.")
        bot_id = bot.me.id
        if user_id not in await get_list_from_vars(bot_id, "PREM_USERS"):
            await add_to_vars(bot_id, "PREM_USERS", user_id)
        await set_expired_date(user_id, _to_jakarta(expires))
        return doc


def _find_client(user_id: int):
    for X in ubot._ubot:
        if X.me and X.me.id == user_id:
            return X
    return None


async def _safe_send(chat_id, text, **kwargs):
    try:
        return await bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        print(f"[TRIAL] kirim ke {chat_id} gagal: {e}")
        return None


async def _broadcast(client, user_id: int):
    for chat_id in GROUP_TRIAL_IDS:
        for _ in range(2):
            try:
                await client.send_message(
                    chat_id, TRIAL_BROADCAST_TEXT, disable_web_page_preview=True
                )
                break
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
            except Exception as e:  # bot dikeluarkan dan sebagainya: lanjut grup lain
                print(f"[TRIAL] broadcast {user_id} ke {chat_id} gagal: {e}")
                break
        await asyncio.sleep(2)


async def _has_paid_during_trial(doc: dict) -> bool:
    user_id = doc["user_id"]
    exp = _to_utc_naive(await get_expired_date(user_id))
    if exp and exp > _to_utc_naive(doc["trial_expires_at"]):
        return True  # masa aktif sudah diperpanjang oleh pembayaran
    paid = await PAID_TRX.find_one(
        {
            "user_id": user_id,
            "status": "paid",
            "paid_at": {"$gte": _to_utc_naive(doc["trial_started_at"])},
        }
    )
    return paid is not None


async def _end_trial(doc: dict):
    user_id = doc["user_id"]
    # Tandai dulu agar tidak diproses dua kali
    res = await TRIALS.update_one(
        {"user_id": user_id, "status": "active"},
        {"$set": {"status": "expired", "ended_at": _utcnow()}},
    )
    if res.modified_count == 0:
        return
    if await _has_paid_during_trial(doc):
        print(f"[TRIAL] {user_id} sudah berbayar, trial berakhir tanpa logout")
        return

    await remove_from_vars(bot.me.id, "PREM_USERS", user_id)
    client = _find_client(user_id)
    if client is not None:
        try:
            await client.unblock_user(bot.me.username)
        except Exception:
            pass
        ubot._ubot.remove(client)
        if user_id in ubot._get_my_id:
            ubot._get_my_id.remove(user_id)
        try:
            await client.log_out()
        except Exception as e:
            print(f"[TRIAL] log_out {user_id} gagal: {e}")
    await remove_ubot(user_id)
    await remove_all_vars(user_id)
    await rem_expired_date(user_id)
    await _safe_send(
        user_id,
        "<b>⌛ Masa trial Anda sudah habis</b>\n\n"
        "Userbot Anda telah dinonaktifkan. Pilih paket berbayar untuk melanjutkan.",
        reply_markup=_expired_markup(),
    )


def _expired_markup():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("💳 Bayar Dulu", callback_data="bayar_dulu")]]
    )


async def _tick():
    now = _utcnow()
    docs = await TRIALS.find({"status": "active"}).to_list(None)
    for doc in docs:
        user_id = doc["user_id"]
        try:
            if now >= _to_utc_naive(doc["trial_expires_at"]):
                await _end_trial(doc)
                continue
            last = _to_utc_naive(doc.get("last_broadcast_at"))
            if last is not None and now - last < timedelta(hours=TRIAL_BROADCAST_HOURS):
                continue
            client = _find_client(user_id)
            if client is None:
                continue  # userbot belum/tidak berjalan; dicoba lagi nanti
            await _broadcast(client, user_id)
            await TRIALS.update_one(
                {"user_id": user_id, "status": "active"},
                {"$set": {"last_broadcast_at": now}},
            )
        except Exception as e:
            print(f"[TRIAL] proses {user_id} gagal: {e}")


async def trial_scheduler():
    """Loop tiap 60 detik: broadcast berkala dan pengakhiran trial."""
    try:
        await TRIALS.create_index("user_id", unique=True)
    except Exception as e:
        print(f"[TRIAL] index gagal dibuat: {e}")
    while True:
        try:
            await _tick()
        except Exception as e:
            print(f"[TRIAL] scheduler error: {e}")
        await asyncio.sleep(60)
