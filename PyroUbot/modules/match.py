from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, MessageNotModified

from PyroUbot import *

# Diimpor SETELAH star import: PyroUbot.core.helpers.tools mengekspor `time`
# (fungsi), yang akan menimpa modul `time` jika diimpor di atas.
import asyncio  # noqa: E402
from time import monotonic  # noqa: E402

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

# Animasi selesai paling lama MAX_TOTAL detik dari edit pertama sampai frame terakhir.
FRAME_DELAY = 0.2
MAX_TOTAL = 1.9
# FloodWait di atas batas ini tidak ditunggu: sticker dikirim tanpa edit lagi.
MAX_FLOOD_WAIT = 3
MAX_FRAMES = 6


def _dedupe(frames):
    out = []
    for frame in frames:
        if not out or out[-1] != frame:
            out.append(frame)
    return out


# .m1 : ketik per bagian, roket melintas, lalu api
M1_WORDS = ["MATCH", "PERTAMA!", "SIAPA", "YANG", "AMANIN", "POINT", "DULU,", "K", "ATAU", "B???"]
M1_HEAD = " ".join(M1_WORDS)
M1_FRAMES = [
    " ".join(M1_WORDS[:4]),
    " ".join(M1_WORDS[:7]),
    M1_HEAD,
    "·🚀····",
    "····🚀",
    M1_HEAD + " 🔥",
]

# .m1only : ketik, lalu 🥶 berubah menjadi 🔥 dan 🚀
M1ONLY_WORDS = ["ONLY", "1", "MATCH!", "WHO'S", "WIN,", "K", "ATAU", "B?!!"]
M1ONLY_HEAD = " ".join(M1ONLY_WORDS)
M1ONLY_FRAMES = [
    " ".join(M1ONLY_WORDS[:4]),
    M1ONLY_HEAD,
    f"{M1ONLY_HEAD}\n🥶 🥶 🥶 🥶 🥶",
    f"{M1ONLY_HEAD}\n🥶 🥶 🔥 🔥 🔥",
    f"{M1ONLY_HEAD}\n🔥 🔥 🔥 🔥 🔥",
    f"{M1ONLY_HEAD}\n🔥 🚀",
]

# .m2 : ketik, lalu api menyala bertahap (tepat 3 api di akhir)
M2_WORDS = ["MATCH", "KEDUA!", "APAKAH", "2-0", "ATAU", "LANJUT", "M3?", "KITA", "SAKSIKAN!!!"]
M2_HEAD = " ".join(M2_WORDS)
M2_FRAMES = [
    " ".join(M2_WORDS[:4]),
    " ".join(M2_WORDS[:7]),
    M2_HEAD,
    f"{M2_HEAD}\n🔥",
    f"{M2_HEAD}\n🔥🔥",
    f"{M2_HEAD}\n🔥🔥🔥",
]

# .m3 : nuansa tegang, sirine, hitung mundur 3-2-1, frame akhir dramatis
M3_FRAMES = [
    "OPSS!!! MATCH PENENTUAN!!!",
    "🚨 OPSS!!! MATCH PENENTUAN!!! 🚨\n😱 SIAPA YANG BISA BERTAHAN?",
    "😰 3...",
    "⚔️ 2...",
    "💀 1...\n⏳ MATCH PENENTUAN DIMULAI... 🔥 GAS!!! 🔥",
    "💀⚔️ OPSS!!! MATCH PENENTUAN!!! ⚔️💀\n🔥 TIDAK ADA KATA KEDUA 🔥😱",
]

# cmd -> (nama var sticker, frames)
COMMANDS = {
    "m1": ("M1_STICKER", M1_FRAMES),
    "m1only": ("M1ONLY_STICKER", M1ONLY_FRAMES),
    "m2": ("M2_STICKER", M2_FRAMES),
    "m3": ("M3_STICKER", M3_FRAMES),
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
    """Edit pesan animasi. False jika gagal; FloodWait diteruskan ke pemanggil."""
    try:
        await msg.edit(text, parse_mode=ParseMode.DISABLED)
        return True
    except MessageNotModified:
        return True
    except FloodWait:
        raise
    except Exception as e:
        print(f"[match] animasi dihentikan: {e}")
        return False


async def _safe_edit(msg, text):
    try:
        return await _edit(msg, text)
    except FloodWait:
        return False


async def _animate(target, frames, start, shown):
    """Tampilkan frame sisa sampai frame terakhir, tanpa melewati MAX_TOTAL.

    shown: indeks frame yang sudah tampil (-1 jika belum ada).
    start: waktu monotonic saat animasi dimulai.
    """
    last = len(frames) - 1
    i = shown
    while True:
        if i < 0:
            nxt = 0  # frame pertama langsung tampil
        elif i >= last:
            return
        elif monotonic() - start + FRAME_DELAY > MAX_TOTAL:
            nxt = last  # sisa waktu tidak cukup: lompat ke frame akhir
        else:
            await asyncio.sleep(FRAME_DELAY)
            nxt = i + 1
        try:
            if not await _edit(target, frames[nxt]):
                return
        except FloodWait as e:
            if nxt != last and e.value <= MAX_FLOOD_WAIT:
                await asyncio.sleep(e.value)
                await _safe_edit(target, frames[last])
            return
        i = nxt


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
            if e.value > MAX_FLOOD_WAIT:
                print(f"[match] sticker ditunda FloodWait {e.value}s")
                return False
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


async def _play(client, message, cmd, var, frames, prefix):
    frames = _dedupe(frames)
    start = monotonic()
    own = bool(
        getattr(message, "outgoing", False)
        or (message.from_user is not None and message.from_user.id == client.me.id)
    )

    if own:
        target = message
        shown = -1
    else:
        # Pesan dari pengirim lain (mis. sudo): jangan edit pesan orang lain.
        try:
            target = await message.reply_text(frames[0], parse_mode=ParseMode.DISABLED)
        except Exception as e:
            print(f"[match] gagal kirim pesan animasi: {e}")
            return
        shown = 0

    await _animate(target, frames, start, shown)

    file_id = await get_vars(client.me.id, var)
    if file_id:
        await _send_sticker(client, message, file_id, cmd, prefix)
    else:
        await message.reply_text(
            f"Belum ada sticker. Reply sticker lalu kirim {prefix}{cmd} save",
            parse_mode=ParseMode.DISABLED,
        )


async def _handle(client, message, cmd):
    var, frames = COMMANDS[cmd]
    prefix = (await ubot.get_prefix(client.me.id))[0]
    args = message.command[1:] if getattr(message, "command", None) else []
    if args and args[0].lower() == "save":
        return await _save(client, message, cmd, var, prefix)
    return await _play(client, message, cmd, var, frames, prefix)


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
