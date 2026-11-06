import asyncio

from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, MessageNotModified

from PyroUbot import *

__MODULE__ = "ᴍᴀᴛᴄʜ"
__HELP__ = """
<blockquote><b>Bantuan Match</b>

• <b>Simpan sticker</b> : reply sebuah sticker lalu kirim
  <code>{0}m1 save</code>, <code>{0}m1only save</code>, <code>{0}m2 save</code>, <code>{0}m3 save</code>
  (save ulang akan menimpa sticker lama)

• <b>Perintah</b> : <code>{0}m1</code>
  • <b>Penjelasan : animasi match pertama lalu sticker.</b>

• <b>Perintah</b> : <code>{0}m1only</code>
  • <b>Penjelasan : animasi only 1 match (beku ke panas) lalu sticker.</b>

• <b>Perintah</b> : <code>{0}m2</code>
  • <b>Penjelasan : animasi match kedua lalu sticker.</b>

• <b>Perintah</b> : <code>{0}m3</code>
  • <b>Penjelasan : animasi match penentuan lalu sticker.</b></blockquote>
"""

_pending = set()
DELETE_AFTER = 5


def _cumulative(words):
    return [" ".join(words[: i + 1]) for i in range(len(words))]


def _dedupe(frames):
    out = []
    for frame in frames:
        if not out or out[-1] != frame:
            out.append(frame)
    return out


# .m1 : ketik per kata, roket melintas, lalu api
M1_WORDS = ["MATCH", "PERTAMA!", "SIAPA", "YANG", "AMANIN", "POINT", "DULU,", "K", "ATAU", "B???"]
M1_HEAD = " ".join(M1_WORDS)
M1_FRAMES = (
    _cumulative(M1_WORDS)
    + ["·" * i + "🚀" + "·" * (5 - i) for i in range(6)]
    + [M1_HEAD + " 🔥"]
)

# .m1only : ketik, lalu 🥶 berubah menjadi 🔥 dan 🚀
M1ONLY_WORDS = ["ONLY", "1", "MATCH!", "WHO'S", "WIN,", "K", "ATAU", "B?!!"]
M1ONLY_HEAD = " ".join(M1ONLY_WORDS)
M1ONLY_ROWS = [
    "🥶 🥶 🥶 🥶 🥶",
    "🥶 🥶 🥶 🥶 🔥",
    "🥶 🥶 🥶 🔥 🔥",
    "🥶 🥶 🔥 🔥 🔥",
    "🥶 🔥 🔥 🔥 🔥",
    "🔥 🔥 🔥 🔥 🔥",
    "🔥 🔥 🔥 🔥 🚀",
    "🚀 🚀 🚀 🚀 🚀",
]
M1ONLY_FRAMES = (
    _cumulative(M1ONLY_WORDS)
    + [f"{M1ONLY_HEAD}\n{row}" for row in M1ONLY_ROWS]
    + [f"{M1ONLY_HEAD}\n🔥 🚀"]
)

# .m2 : ketik, lalu api menyala bertahap (tepat 3 api di akhir)
M2_WORDS = ["MATCH", "KEDUA!", "APAKAH", "2-0", "ATAU", "LANJUT", "M3?", "KITA", "SAKSIKAN!!!"]
M2_HEAD = " ".join(M2_WORDS)
M2_FRAMES = (
    _cumulative(M2_WORDS)
    + [f"{M2_HEAD}\n🔥", f"{M2_HEAD}\n🔥🔥", f"{M2_HEAD}\n🔥🔥🔥"]
)

# .m3 : nuansa tegang, sirine, hitung mundur, frame akhir dramatis
M3_FRAMES = [
    "OPSS!!! MATCH PENENTUAN!!!",
    "🚨 OPSS!!! MATCH PENENTUAN!!! 🚨",
    "🔵 OPSS!!! MATCH PENENTUAN!!! 🔵",
    "🔴 OPSS!!! MATCH PENENTUAN!!! 🔴",
    "🔵 OPSS!!! MATCH PENENTUAN!!! 🔵",
    "🔴 OPSS!!! MATCH PENENTUAN!!! 🔴",
    "😱 SIAPA YANG BISA BERTAHAN?",
    "😰 3...",
    "⚔️ 2...",
    "💀 1...",
    "⏳ MATCH PENENTUAN DIMULAI...",
    "🔥 GAS!!! 🔥",
    "💀⚔️ OPSS!!! MATCH PENENTUAN!!! ⚔️💀\n🔥 TIDAK ADA KATA KEDUA 🔥😱",
]

# cmd -> (key vars sticker, frames, jeda antar edit dalam detik)
COMMANDS = {
    "m1": ("M1_STICKER", M1_FRAMES, 0.7),
    "m1only": ("M1ONLY_STICKER", M1ONLY_FRAMES, 0.7),
    "m2": ("M2_STICKER", M2_FRAMES, 0.8),
    "m3": ("M3_STICKER", M3_FRAMES, 0.8),
}


async def _delete_later(msg):
    await asyncio.sleep(DELETE_AFTER)
    try:
        await msg.delete()
    except Exception:
        pass


async def _notify(message, text):
    """Balas singkat lalu hapus otomatis."""
    try:
        msg = await message.reply_text(text, parse_mode=ParseMode.DISABLED)
    except Exception as e:
        print(f"[match] gagal kirim pesan: {e}")
        return
    task = asyncio.create_task(_delete_later(msg))
    _pending.add(task)
    task.add_done_callback(_pending.discard)


async def _edit(msg, text):
    """Edit pesan animasi. Return False jika animasi harus dihentikan."""
    for _ in range(3):
        try:
            await msg.edit(text, parse_mode=ParseMode.DISABLED)
            return True
        except MessageNotModified:
            return True
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"[match] animasi dihentikan: {e}")
            return False
    return False


async def _save(client, message, cmd, var, prefix):
    reply = message.reply_to_message
    if reply is None or reply.sticker is None:
        return await _notify(
            message, f"Balas sebuah sticker lalu kirim {prefix}{cmd} save."
        )
    await set_vars(client.me.id, var, reply.sticker.file_id)
    await _notify(message, f"Sticker untuk {prefix}{cmd} berhasil disimpan.")


async def _send_sticker(client, message, file_id, cmd, prefix):
    for _ in range(2):
        try:
            await client.send_sticker(message.chat.id, file_id)
            return True
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"[match] gagal kirim sticker: {e}")
            break
    await client.send_message(
        message.chat.id,
        f"Gagal kirim sticker (file_id tidak valid). Reply sticker lalu kirim {prefix}{cmd} save untuk menyimpan ulang.",
        parse_mode=ParseMode.DISABLED,
    )
    return False


async def _play(client, message, cmd, var, frames, delay, prefix):
    frames = _dedupe(frames)
    own = bool(
        getattr(message, "outgoing", False)
        or (message.from_user is not None and message.from_user.id == client.me.id)
    )

    if own:
        target = message
        ok = await _edit(target, frames[0])
    else:
        # Pesan dari pengirim lain (mis. sudo): jangan edit pesan orang lain.
        try:
            target = await message.reply_text(frames[0], parse_mode=ParseMode.DISABLED)
        except Exception as e:
            print(f"[match] gagal kirim pesan animasi: {e}")
            return
        ok = True

    if ok:
        for frame in frames[1:]:
            await asyncio.sleep(delay)
            if not await _edit(target, frame):
                break  # tetap lanjut ke pengiriman sticker

    file_id = await get_vars(client.me.id, var)
    if file_id:
        await _send_sticker(client, message, file_id, cmd, prefix)
    else:
        await message.reply_text(
            f"Belum ada sticker. Reply sticker lalu kirim {prefix}{cmd} save",
            parse_mode=ParseMode.DISABLED,
        )


async def _handle(client, message, cmd):
    var, frames, delay = COMMANDS[cmd]
    prefix = (await ubot.get_prefix(client.me.id))[0]
    args = message.command[1:] if getattr(message, "command", None) else []
    if args and args[0].lower() == "save":
        return await _save(client, message, cmd, var, prefix)
    return await _play(client, message, cmd, var, frames, delay, prefix)


@PY.UBOT("m1")
async def _(client, message):
    await _handle(client, message, "m1")


@PY.UBOT("m1only")
async def _(client, message):
    await _handle(client, message, "m1only")


@PY.UBOT("m2")
async def _(client, message):
    await _handle(client, message, "m2")


@PY.UBOT("m3")
async def _(client, message):
    await _handle(client, message, "m3")
