from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from PyroUbot import *


def _verify_markup(user_id):
    rows = [
        [InlineKeyboardButton(f"➕ Join Grup {i}", url=link)]
        for i, link in enumerate(TRIAL_GROUP_LINKS, start=1)
    ]
    rows.append([InlineKeyboardButton("✅ Coba Lagi", callback_data="trial_check")])
    rows.append([InlineKeyboardButton("⬅ Kembali", callback_data=f"home {user_id}")])
    return InlineKeyboardMarkup(rows)


def _buat_markup():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔥 Buat Userbot 🔥", callback_data="buat_ubot")]]
    )


def _bayar_markup():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("💳 Bayar Dulu", callback_data="bayar_dulu")]]
    )


async def _edit(callback_query, text, markup):
    try:
        await callback_query.edit_message_text(
            text, disable_web_page_preview=True, reply_markup=markup
        )
    except MessageNotModified:
        pass


@PY.CALLBACK("^trial_start$")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    if await trial_is_paid_premium(user_id):
        return await _edit(
            callback_query,
            "<b>✅ Akun Anda sudah premium.</b>\n\nSilakan buat userbot.",
            _buat_markup(),
        )
    status, doc = await trial_status(user_id)
    if status == "active":
        return await _edit(
            callback_query,
            f"<b>✅ Trial Anda sedang aktif</b>\nAktif sampai: {format_wib(doc['trial_expires_at'])} WIB",
            _buat_markup(),
        )
    if status == "expired":
        return await _edit(
            callback_query,
            "<b>❌ Trial sudah pernah digunakan</b>\n\nSilakan pilih paket berbayar.",
            _bayar_markup(),
        )
    await _edit(
        callback_query,
        f"<b>🎁 Coba Trial {TRIAL_DAYS} hari</b>\n\n"
        "Join ketiga grup berikut terlebih dahulu, lalu tekan <b>Coba Lagi</b>.",
        _verify_markup(user_id),
    )


@PY.CALLBACK("^trial_check$")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    if await trial_is_paid_premium(user_id):
        return await _edit(
            callback_query,
            "<b>✅ Akun Anda sudah premium.</b>\n\nSilakan buat userbot.",
            _buat_markup(),
        )
    status, doc = await trial_status(user_id)
    if status == "active":
        return await _edit(
            callback_query,
            f"<b>✅ Trial Anda sudah aktif</b>\nAktif sampai: {format_wib(doc['trial_expires_at'])} WIB",
            _buat_markup(),
        )
    if status == "expired":
        return await _edit(
            callback_query,
            "<b>❌ Trial sudah pernah digunakan</b>\n\nSilakan pilih paket berbayar.",
            _bayar_markup(),
        )

    try:
        missing = await trial_missing_groups(user_id)
    except TrialGroupError as e:
        try:
            await bot.send_message(
                OWNER_ID,
                f"<b>⚠️ Verifikasi trial gagal</b>\n"
                f"Bot belum bisa mengecek grup <code>{e.chat_id}</code>: {e.reason}\n"
                "Pastikan bot adalah anggota/admin di semua grup trial.",
            )
        except Exception as err:
            print(f"[TRIAL] notif owner gagal: {err}")
        return await callback_query.answer(
            "Verifikasi grup sedang bermasalah. Coba lagi nanti.", show_alert=True
        )

    if missing:
        names = ", ".join(f"Grup {i}" for i in missing)
        return await _edit(
            callback_query,
            f"<b>❌ Anda belum join: {names}</b>\n\n"
            "Join grup tersebut, lalu tekan <b>Coba Lagi</b>.",
            _verify_markup(user_id),
        )

    try:
        doc = await trial_activate(user_id)
    except TrialError as e:
        return await callback_query.answer(str(e), show_alert=True)

    await _edit(
        callback_query,
        f"<b>✅ Trial {TRIAL_DAYS} hari aktif</b>\n"
        f"Aktif sampai: {format_wib(doc['trial_expires_at'])} WIB\n\n"
        "Tekan tombol di bawah untuk membuat userbot Anda.",
        _buat_markup(),
    )
