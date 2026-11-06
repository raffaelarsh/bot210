import asyncio
from datetime import datetime
from io import BytesIO

import httpx
from dateutil.relativedelta import relativedelta
from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pytz import timezone

from PyroUbot import *

CONFIRM_PAYMENT = []


@PY.CALLBACK("^confirm")
async def _(client, callback_query):
    user_id = int(callback_query.from_user.id)
    full_name = f"{callback_query.from_user.first_name} {callback_query.from_user.last_name or ''}"
    get = await bot.get_users(user_id)
    CONFIRM_PAYMENT.append(get.id)
    try:
        await callback_query.message.delete()
        pesan = await bot.ask(
            user_id,
            f"""
<blockquote><b>ꜱɪʟᴀʜᴋᴀɴ ᴍᴇʟᴀᴋᴜᴋᴀɴ ᴘᴇᴍʙᴀʏᴀʀᴀɴ ᴛᴇʀʟᴇʙɪʜ ᴛᴀʜᴜʟᴜ ᴋᴇ ᴅᴀɴᴀ ᴅɪ ʙᴀᴡᴀʜ ɪɴɪ</b>           

ᴅᴀɴᴀ : || '089619601820` ||

<b>💬 sɪʟᴀʜᴋᴀɴ ᴋɪʀɪᴍᴋᴀɴ ʙᴜᴋᴛɪ sᴄʀᴇᴇɴsʜᴏᴛ ᴘᴇᴍʙᴀʏᴀʀᴀɴ ᴀɴᴅᴀ: {full_name}</b></blockquote>
""",
            timeout=300,
        )
    except asyncio.TimeoutError as out:
        return await bot.send_message(get.id, "ᴘᴇᴍʙᴀᴛᴀʟᴀɴ ᴏᴛᴏᴍᴀᴛɪs")
    if get.id in CONFIRM_PAYMENT:
        if not pesan.photo:
            CONFIRM_PAYMENT.remove(get.id)
            buttons = [[InlineKeyboardButton("✅ ᴋᴏɴꜰɪʀᴍᴀsɪ", callback_data="confirm")]]
            return await bot.send_message(
                user_id,
                """
<blockquote><b>❌ ᴛɪᴅᴀᴋ ᴅᴀᴘᴀᴛ ᴅɪᴘʀᴏsᴇs</b>

<b>💬 ʜᴀʀᴀᴘ ᴋɪʀɪᴍᴋᴀɴ sᴄʀᴇᴇɴsʜᴏᴛ ʙᴜᴋᴛɪ ᴘᴇᴍʙᴀʏᴀʀᴀɴ ᴀɴᴅᴀ ʏᴀɴɢ ᴠᴀʟɪᴅ</b>

<b>✅ sɪʟᴀʜᴋᴀɴ ᴋᴏɴꜰɪʀᴍᴀsɪ ᴜʟᴀɴɢ ᴘᴇᴍʙᴀʏᴀʀᴀɴ ᴀɴᴅᴀ</b></blockquote>
""",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        elif pesan.photo:
            buttons = BTN.ADD_EXP(get.id)
            await pesan.copy(
                OWNER_ID,
                reply_markup=buttons,
            )
            CONFIRM_PAYMENT.remove(get.id)
            buttons = [
                [InlineKeyboardButton("📞 ᴏᴡɴᴇʀ", url="https://t.me/anyonima")]
            ]
            return await bot.send_message(
                user_id,
                f"""
<blockquote><b>💬 ʙᴀɪᴋ {full_name} sɪʟᴀʜᴋᴀɴ ᴅɪᴛᴜɴɢɢᴜ ᴅᴀɴ ᴊᴀɴɢᴀɴ sᴘᴀᴍ ʏᴀ</b>

<b>🏦 ᴘᴇᴍʙᴀʏᴀʀᴀɴ ᴀɴᴅᴀ ᴀᴋᴀɴ ᴅɪᴋᴏɴꜰɪʀᴍᴀsɪ sᴇᴛᴇʟᴀʜ 1-2 ᴊᴀᴍ ᴋᴇʀᴊᴀ</b></blockquote>
""",
                reply_markup=InlineKeyboardMarkup(buttons),
            )


@PY.CALLBACK("^(kurang|tambah)")
async def _(client, callback_query):
    action, _, raw_days = callback_query.data.partition(" ")
    paket = sorted(PREMIUM_PLANS)
    try:
        idx = paket.index(int(raw_days))
    except ValueError:
        idx = 0
    if action == "kurang" and idx > 0:
        idx -= 1
    elif action == "tambah" and idx < len(paket) - 1:
        idx += 1
    days = paket[idx]
    buttons = BTN.PLUS_MINUS(days, callback_query.from_user.id)
    try:
        await callback_query.message.edit_text(
            MSG.TEXT_PAYMENT(days, PREMIUM_PLANS[days]),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except MessageNotModified:
        pass
    await callback_query.answer()


@PY.CALLBACK("^qris_pay \\d+$")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    try:
        days = int(callback_query.data.split()[1])
    except (IndexError, ValueError):
        return await callback_query.answer("Paket tidak valid.", show_alert=True)
    try:
        trx = await create_qris(user_id, days)
    except AutoGoPayError as e:
        return await callback_query.answer(str(e)[:190], show_alert=True)

    caption = (
        "<b>⚡ Pembayaran QRIS Otomatis</b>\n\n"
        f"Durasi: {trx['days']} hari\n"
        f"Total bayar: {format_rupiah(trx['amount'])}\n"
        f"ID transaksi: <code>{trx['_id']}</code>\n\n"
        "Cara bayar: scan QR di atas memakai GoPay atau aplikasi pembayaran QRIS lain. "
        "Premium aktif otomatis setelah pembayaran terdeteksi.\n"
        f"Berlaku sampai: {format_wib(trx['expires_at'])} WIB"
    )
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Batalkan QRIS", callback_data="qris_cancel")]]
    )
    try:
        msg = await bot.send_photo(user_id, trx["qr_url"], caption=caption, reply_markup=markup)
    except Exception:
        try:
            async with httpx.AsyncClient(timeout=20) as http:
                resp = await http.get(trx["qr_url"])
                resp.raise_for_status()
            image = BytesIO(resp.content)
            image.name = "qris.png"
            msg = await bot.send_photo(user_id, image, caption=caption, reply_markup=markup)
        except Exception as e:
            print(f"[AUTOGOPAY] gagal mengirim QR {trx['_id']}: {e}")
            await cancel_pending(user_id)
            return await callback_query.answer(
                "Gagal menampilkan QRIS, coba lagi.", show_alert=True
            )

    await attach_message(trx["_id"], msg.chat.id, msg.id)
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.answer()


@PY.CALLBACK("^qris_cancel$")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    try:
        state, _trx = await cancel_pending(user_id, apply_cooldown=True)
    except AutoGoPayError as e:
        return await callback_query.answer(str(e)[:190], show_alert=True)

    if state == "paid":
        await callback_query.answer(
            "Pembayaran sudah berhasil. Premium Anda sudah aktif.", show_alert=True
        )
        return
    if state == "none":
        return await callback_query.answer("Tidak ada QRIS yang perlu dibatalkan.", show_alert=True)

    await callback_query.answer()
    await bot.send_message(
        user_id,
        "<b>❌ QRIS dibatalkan</b>\n\n"
        f"Untuk mencegah spam, Anda bisa membuat QRIS baru dalam "
        f"{QRIS_CANCEL_COOLDOWN_MINUTES} menit.",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("💳 Bayar Dulu", callback_data="bayar_dulu")],
                [InlineKeyboardButton("⬅ Kembali", callback_data=f"home {user_id}")],
            ]
        ),
    )


@PY.CALLBACK("^(success|failed|home)")
async def _(client, callback_query):
    query = callback_query.data.split()
    get_user = await bot.get_users(query[1])
    if query[0] == "success":
        buttons = [
            [InlineKeyboardButton("🔥 ʙᴜᴀᴛ ᴜsᴇʀʙᴏᴛ 🔥", callback_data="buat_ubot")],
        ]
        await bot.send_message(
            get_user.id,
            f"""
<blockquote><b>✅ ᴘᴇᴍʙᴀʏᴀʀᴀɴ ᴀɴᴅᴀ ʙᴇʀʜᴀsɪʟ ᴅɪᴋᴏɴꜰɪʀᴍᴀsɪ</b>

<b>💬 sᴇᴋᴀʀᴀɴɢ ᴀɴᴅᴀ ʙɪsᴀ ᴍᴇᴍʙᴜᴀᴛ ᴜsᴇʀʙᴏᴛ</b></blockquote>
""",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        buttons_success = [
            [
                InlineKeyboardButton(
                    "👤 ᴅᴀᴘᴀᴛᴋᴀɴ ᴘʀᴏꜰɪʟ 👤", callback_data=f"profil {get_user.id}"
                )
            ],
        ]
        await add_to_vars(client.me.id, "PREM_USERS", get_user.id)
        now = datetime.now(timezone("Asia/Jakarta"))
        expired = now + relativedelta(months=int(query[2]))
        await set_expired_date(get_user.id, expired)
        return await callback_query.edit_message_text(
            f"""
<blockquote><b>✅ {get_user.first_name} {get_user.last_name or ''} ᴅɪᴛᴀᴍʙᴀʜᴋᴀɴ ᴋᴇ ᴀɴɢɢᴏᴛᴀ ᴘʀᴇᴍɪᴜᴍ</b></blockquote>
""",
        )
    if query[0] == "failed":
        buttons = [
            [
                InlineKeyboardButton(
                    "💳 ʟᴀᴋᴜᴋᴀɴ ᴘᴇᴍʙᴀʏᴀʀᴀɴ 💳", callback_data="bayar_dulu"
                )
            ],
        ]
        await bot.send_message(
            get_user.id,
            """
<b>❌ ᴘᴇᴍʙᴀʏᴀʀᴀɴ ᴀɴᴅᴀ ᴛɪᴅᴀᴋ ʙɪsᴀ ᴅɪᴋᴏɴꜰɪʀᴍᴀsɪ</b>

<b>💬 sɪʟᴀʜᴋᴀɴ ʟᴀᴋᴜᴋᴀɴ ᴘᴇᴍʙᴀʏᴀʀᴀɴ ᴅᴇɴɢᴀɴ ʙᴇɴᴀʀ</b>
""",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        buttons_failed = [
            [
                InlineKeyboardButton(
                    "👤 ᴅᴀᴘᴀᴛᴋᴀɴ ᴘʀᴏꜰɪʟ 👤", callback_data=f"profil {get_user.id}"
                )
            ],
        ]
        return await callback_query.edit_message_text(
            f"""
<b>❌ {get_user.first_name} {get_user.last_name or ''} ᴛɪᴅᴀᴋ ᴅɪᴛᴀᴍʙᴀʜᴋᴀɴ ᴋᴇ ᴀɴɢɢᴏᴛᴀ ᴘʀᴇᴍɪᴜᴍ</b>
""",
        )
    if query[0] == "home":
        if get_user.id in CONFIRM_PAYMENT:
            CONFIRM_PAYMENT.remove(get_user.id)
            buttons_home = BTN.START(callback_query)
            return await callback_query.edit_message_text(
                MSG.START(callback_query),
                reply_markup=InlineKeyboardMarkup(buttons_home),
            )
        else:
            buttons_home = BTN.START(callback_query)
            return await callback_query.edit_message_text(
                MSG.START(callback_query),
                reply_markup=InlineKeyboardMarkup(buttons_home),
            )
