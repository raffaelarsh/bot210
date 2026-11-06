"""Pembayaran QRIS otomatis via AutoGoPay.

Kontrak API (sama dengan bot sanzbot):
  POST /qris/generate  {"amount": int}           -> data.transaction_id, data.qr_url
  POST /qris/status    {"transaction_id": str}   -> data.transaction_status
  POST /qris/cancel    {"transaction_id": str}
Semua request memakai header Authorization: Bearer <AUTOGOPAY_API_KEY>.

Alur sukses dibuat idempoten:
  pending -> processing (klaim atomik, new_expire disimpan) -> paid
"""

import asyncio
from datetime import datetime, timedelta, timezone as dt_timezone

import httpx
import pytz
from pymongo import ReturnDocument
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from PyroUbot import bot
from PyroUbot.config import (
    AUTOGOPAY_API_KEY,
    AUTOGOPAY_BASE_URL,
    OWNER_ID,
    PREMIUM_PLANS,
    QRIS_EXPIRE_MINUTES,
    QRIS_POLL_INTERVAL,
)
from PyroUbot.core.database import mongodb
from PyroUbot.core.database.expired import get_expired_date, set_expired_date
from PyroUbot.core.database.variabel import add_to_vars, get_list_from_vars

__all__ = [
    "AutoGoPayError",
    "create_qris",
    "attach_message",
    "cancel_pending",
    "autogopay_poller",
    "format_wib",
    "format_rupiah",
]

TRX = mongodb["autogopay_trx"]
JAKARTA = pytz.timezone("Asia/Jakarta")

# Status gateway yang berarti transaksi sudah tidak bisa dibayar
GATEWAY_DEAD = {"expire", "expired", "cancel", "cancelled", "deny", "denied", "failure", "failed"}
# Transaksi "processing" yang klaimnya lebih tua dari ini dianggap sisa crash
CLAIM_STALE_SECONDS = 60

_locks: dict = {}


class AutoGoPayError(Exception):
    """Pesan aman untuk ditampilkan ke user."""


# ── util waktu & format ───────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(dt_timezone.utc).replace(tzinfo=None)


def _to_utc_naive(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt  # Mongo / data naive dianggap UTC
    return dt.astimezone(dt_timezone.utc).replace(tzinfo=None)


def _to_jakarta(dt):
    return pytz.utc.localize(_to_utc_naive(dt)).astimezone(JAKARTA)


def format_wib(dt) -> str:
    return _to_jakarta(dt).strftime("%d-%m-%Y %H:%M")


def format_rupiah(amount: int) -> str:
    return "Rp " + f"{int(amount):,}".replace(",", ".")


def _user_lock(user_id: int) -> asyncio.Lock:
    return _locks.setdefault(user_id, asyncio.Lock())


# ── klien HTTP AutoGoPay ──────────────────────────────────────────

def _require_key():
    if not AUTOGOPAY_API_KEY:
        raise AutoGoPayError(
            "Pembayaran QRIS belum dikonfigurasi (AUTOGOPAY_API_KEY kosong). Hubungi admin."
        )


async def _post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            AUTOGOPAY_BASE_URL.rstrip("/") + path,
            json=body,
            headers={"Authorization": f"Bearer {AUTOGOPAY_API_KEY}"},
        )
    try:
        data = resp.json()
    except ValueError:
        data = {}
    return data if isinstance(data, dict) else {}


async def _gw(path: str, body: dict) -> dict:
    """Panggil gateway, kembalikan isi 'data'. Error httpx dibiarkan naik."""
    _require_key()
    res = await _post(path, body)
    if not res.get("success"):
        raise AutoGoPayError("Gagal memproses permintaan pembayaran, coba lagi.")
    return res.get("data") or {}


async def _safe_status(tx_id: str) -> str:
    try:
        data = await _gw("/qris/status", {"transaction_id": tx_id})
    except httpx.HTTPError:
        raise AutoGoPayError("Gagal memeriksa status pembayaran, coba lagi.")
    return str(data.get("transaction_status", "")).lower()


async def get_status(tx_id: str) -> str:
    return await _safe_status(tx_id)


async def _cancel_remote(tx_id: str):
    try:
        await _gw("/qris/cancel", {"transaction_id": tx_id})
    except Exception as e:  # gagal cancel di gateway tidak membatalkan keputusan lokal
        print(f"[AUTOGOPAY] cancel {tx_id} gagal: {e}")


# ── pengiriman pesan (selalu aman) ────────────────────────────────

async def _safe_send(chat_id, text, **kwargs):
    try:
        return await bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        print(f"[AUTOGOPAY] kirim ke {chat_id} gagal: {e}")
        return None


async def _delete_qr(doc: dict):
    chat_id, message_id = doc.get("chat_id"), doc.get("message_id")
    if not chat_id or not message_id:
        return
    try:
        await bot.delete_messages(chat_id, message_id)
    except Exception as e:
        print(f"[AUTOGOPAY] hapus pesan QR gagal: {e}")


async def _notify_paid(doc: dict):
    uid = doc["user_id"]
    exp = _to_jakarta(doc["new_expire"]).strftime("%d-%m-%Y")
    await _safe_send(
        uid,
        f"<b>✅ Pembayaran QRIS berhasil</b>\n\n"
        f"Durasi: {doc['days']} hari\n"
        f"Nominal: {format_rupiah(doc['amount'])}\n"
        f"Aktif sampai: {exp}\n\n"
        f"Sekarang Anda bisa membuat userbot.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔥 Buat Userbot 🔥", callback_data="buat_ubot")]]
        ),
    )
    await _safe_send(
        OWNER_ID,
        f"<b>💰 Pembayaran QRIS diterima</b>\n"
        f"User: <a href=tg://user?id={uid}>{uid}</a>\n"
        f"Trx: <code>{doc['_id']}</code>\n"
        f"Durasi: {doc['days']} hari\n"
        f"Nominal: {format_rupiah(doc['amount'])}",
    )
    await _delete_qr(doc)


async def _notify_expired(doc: dict):
    await _safe_send(
        doc["user_id"],
        "<b>⌛ QRIS sudah kedaluwarsa atau dibatalkan</b>\n\n"
        "Silakan pilih paket dan buat QRIS baru.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("💳 Bayar Dulu", callback_data="bayar_dulu")]]
        ),
    )
    await _delete_qr(doc)


# ── aktivasi premium (idempoten lewat new_expire tersimpan) ───────

async def _activate_premium(user_id: int, new_expire_utc: datetime):
    bot_id = bot.me.id
    if user_id not in await get_list_from_vars(bot_id, "PREM_USERS"):
        await add_to_vars(bot_id, "PREM_USERS", user_id)
    await set_expired_date(user_id, _to_jakarta(new_expire_utc))


async def _finish_paid(doc: dict):
    """Dipanggil setelah klaim berhasil (status 'processing')."""
    await _activate_premium(doc["user_id"], _to_utc_naive(doc["new_expire"]))
    await TRX.update_one(
        {"_id": doc["_id"]}, {"$set": {"status": "paid", "paid_at": _utcnow()}}
    )
    await _notify_paid(doc)


async def _process_paid(doc: dict) -> bool:
    """Klaim atomik pending -> processing, lalu aktifkan premium.

    Mengembalikan False jika transaksi sudah diklaim/diproses oleh pihak lain.
    """
    now = _utcnow()
    current = _to_utc_naive(await get_expired_date(doc["user_id"]))
    base = max(now, current) if current else now
    new_expire = base + timedelta(days=doc["days"])
    claimed = await TRX.find_one_and_update(
        {"_id": doc["_id"], "status": "pending"},
        {"$set": {"status": "processing", "claimed_at": now, "new_expire": new_expire}},
        return_document=ReturnDocument.AFTER,
    )
    if claimed is None:
        return False
    await _finish_paid(claimed)
    return True


async def _recover_stale():
    cutoff = _utcnow() - timedelta(seconds=CLAIM_STALE_SECONDS)
    docs = await TRX.find(
        {"status": "processing", "claimed_at": {"$lt": cutoff}}
    ).to_list(None)
    for doc in docs:
        taken = await TRX.find_one_and_update(
            {"_id": doc["_id"], "status": "processing", "claimed_at": {"$lt": cutoff}},
            {"$set": {"claimed_at": _utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        if taken:
            print(f"[AUTOGOPAY] memulihkan transaksi {doc['_id']}")
            await _finish_paid(taken)


# ── penutupan transaksi pending ───────────────────────────────────

async def _close_trx(doc: dict, new_status: str) -> str:
    """Tandai pending -> new_status setelah memastikan belum settlement.

    Hasil: "closed" (benar-benar ditutup), "paid" (ternyata sudah dibayar,
    sudah dikembalikan ke pending agar bisa diproses), "gone" (sudah berubah).
    """
    tx = doc["_id"]
    res = await TRX.update_one(
        {"_id": tx, "status": "pending"},
        {"$set": {"status": new_status, "closed_at": _utcnow()}},
    )
    if res.modified_count == 0:
        return "gone"
    try:
        status = await _safe_status(tx)
    except Exception:
        await TRX.update_one({"_id": tx, "status": new_status}, {"$set": {"status": "pending"}})
        raise
    if status == "settlement":
        await TRX.update_one({"_id": tx, "status": new_status}, {"$set": {"status": "pending"}})
        return "paid"
    await _cancel_remote(tx)
    return "closed"


async def _resolve_pending_locked(user_id: int):
    """Tutup/proses semua QRIS pending milik user. Dipanggil dengan lock user."""
    docs = await TRX.find({"user_id": user_id, "status": "pending"}).to_list(None)
    result = ("none", None)
    for doc in docs:
        outcome = await _close_trx(doc, "cancelled")
        if outcome == "paid":
            await _process_paid(doc)
            return "paid", doc
        if outcome == "gone":
            fresh = await TRX.find_one({"_id": doc["_id"]})
            if fresh and fresh.get("status") in ("processing", "paid"):
                return "paid", fresh
            continue
        await _delete_qr(doc)
        result = ("cancelled", doc)
    return result


# ── API publik ────────────────────────────────────────────────────

async def create_qris(user_id: int, days: int) -> dict:
    """Buat QRIS baru untuk paket `days`. Mengembalikan dokumen transaksi."""
    if days not in PREMIUM_PLANS:
        raise AutoGoPayError("Paket durasi tidak tersedia.")
    _require_key()
    async with _user_lock(user_id):
        state, _ = await _resolve_pending_locked(user_id)
        if state == "paid":
            raise AutoGoPayError(
                "Pembayaran QRIS sebelumnya sudah berhasil. Premium Anda sudah aktif."
            )
        amount = PREMIUM_PLANS[days]
        try:
            data = await _gw("/qris/generate", {"amount": amount})
        except httpx.HTTPError:
            raise AutoGoPayError("Server pembayaran tidak dapat dihubungi, coba lagi.")
        tx_id = str(data.get("transaction_id") or "")
        qr_url = data.get("qr_url")
        if not tx_id or not qr_url:
            raise AutoGoPayError("Respons pembayaran tidak valid, coba lagi.")
        now = _utcnow()
        doc = {
            "_id": tx_id,
            "user_id": user_id,
            "days": days,
            "amount": amount,
            "qr_url": qr_url,
            "status": "pending",
            "chat_id": None,
            "message_id": None,
            "created_at": now,
            "expires_at": now + timedelta(minutes=QRIS_EXPIRE_MINUTES),
            "claimed_at": None,
            "new_expire": None,
        }
        await TRX.insert_one(doc)
        return doc


async def attach_message(tx_id: str, chat_id: int, message_id: int):
    await TRX.update_one(
        {"_id": tx_id}, {"$set": {"chat_id": chat_id, "message_id": message_id}}
    )


async def cancel_pending(user_id: int):
    """Batalkan QRIS pending user. Mengembalikan (state, trx)."""
    async with _user_lock(user_id):
        return await _resolve_pending_locked(user_id)


async def _check_pending(doc: dict):
    tx = doc["_id"]
    status = await _safe_status(tx)  # cek gateway dulu, sebelum memutuskan expired
    if status == "settlement":
        await _process_paid(doc)
        return
    timed_out = doc["expires_at"] <= _utcnow()
    if not (timed_out or status in GATEWAY_DEAD):
        return
    outcome = await _close_trx(doc, "expired")
    if outcome == "paid":
        await _process_paid(doc)
    elif outcome == "closed":
        await _notify_expired(doc)


async def poll_once():
    """Satu siklus pengecekan. Error per transaksi tidak menghentikan siklus."""
    if not AUTOGOPAY_API_KEY:
        return
    try:
        await _recover_stale()
    except Exception as e:
        print(f"[AUTOGOPAY] recovery ditunda: {e}")
    docs = await TRX.find({"status": "pending"}).to_list(None)
    for doc in docs:
        try:
            await _check_pending(doc)
        except Exception as e:  # error sementara: coba lagi siklus berikut
            print(f"[AUTOGOPAY] cek {doc['_id']} ditunda: {e}")


async def autogopay_poller():
    """Loop selamanya: cek transaksi pending dan lanjutkan sisa crash."""
    while True:
        try:
            await poll_once()
        except Exception as e:
            print(f"[AUTOGOPAY] poller error: {e}")
        await asyncio.sleep(QRIS_POLL_INTERVAL)
