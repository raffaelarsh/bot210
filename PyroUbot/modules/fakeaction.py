from asyncio import sleep
from pyrogram import enums, filters
from pyrogram.raw import functions
from pyrogram.types import Message
from PyroUbot import *

__MODULE__ = "ғᴀᴋᴇ ᴀᴄᴛɪᴏɴ"
__HELP__ = """
<b>⦪ ʙᴀɴᴛᴜᴀɴ ᴜɴᴛᴜᴋ ғᴀᴋᴇ ᴀᴄᴛɪᴏɴ ⦫</b>

<blockquote>⎆ perintah :
ᚗ <code>{0}ftyping</code> detik
⊶ Menampilkan pengetikan palsu dalam obrolan.

ᚗ <code>{0}fgame</code> detik 
⊶ Menampilkan sedang bermain game palsu dalam obrolan.

ᚗ <code>{0}faudio</code> detik 
⊶ Menampilkan tindakan merekam suara palsu dalam obrolan.

ᚗ <code>{0}fvideo</code> detik 
⊶ Menampilkan tindakan merekam video palsu dalam obrolan.

ᚗ <code>{0}fround</code> detik 
⊶ Menampilkan tindakan merekam video note palsu dalam obrolan.

ᚗ <code>{0}fphoto</code> detik 
⊶ Menampilkan tindakan mengirim foto palsu dalam obrolan.

ᚗ <code>{0}fsticker</code> detik 
⊶ Menampilkan tindakan memilih sticker palsu dalam obrolan.

ᚗ <code>{0}fcontact</code> detik 
⊶ Menampilkan tindakan membagikan kontak palsu dalam obrolan

ᚗ <code>{0}flocation</code> detik 
⊶ Menampilkan tindakan membagikan lokasi palsu dalam obrolan.

ᚗ <code>{0}fdocument</code> detik 
⊶ Menampilkan tindakan mengirim dokumen palsu dalam obrolan.

ᚗ <code>{0}fscreenshot</code> detik 
⊶ Menampilkan tindakan screenshot palsu (Gunakan di Obrolan Pribadi).

ᚗ <code>{0}fstop</code> detik 
⊶ Menghentikan semua tindakan palsu dalam obrolan.</blockquote>
"""

actions = {
    "ftyping": enums.ChatAction.TYPING,
    "fvideo": enums.ChatAction.RECORD_VIDEO,
    "faudio": enums.ChatAction.RECORD_AUDIO,
    "fround": enums.ChatAction.RECORD_VIDEO_NOTE,
    "fphoto": enums.ChatAction.UPLOAD_PHOTO,
    "fsticker": enums.ChatAction.CHOOSE_STICKER,
    "fdocument": enums.ChatAction.UPLOAD_DOCUMENT,
    "flocation": enums.ChatAction.FIND_LOCATION,
    "fgame": enums.ChatAction.PLAYING,
    "fcontact": enums.ChatAction.CHOOSE_CONTACT,
    "fstop": enums.ChatAction.CANCEL,
}


async def send_fake_action(client, message: Message, action):
    try:
        sec = int(message.command[1]) if len(message.command) > 1 else None
        if sec and sec > 60:
            sec = 60
    except ValueError:
        sec = None

    await message.delete()

    if action == enums.ChatAction.CANCEL:
        return await client.send_chat_action(chat_id=message.chat.id, action=action)

    if sec:
        await client.send_chat_action(chat_id=message.chat.id, action=action)
        await sleep(sec)
    else:
        await client.send_chat_action(chat_id=message.chat.id, action=action)


@PY.UBOT("ftyping")
async def fake_typing(client, message: Message):
    await send_fake_action(client, message, enums.ChatAction.TYPING)


@PY.UBOT("fgame")
async def fake_game(client, message: Message):
    await send_fake_action(client, message, enums.ChatAction.PLAYING)


@PY.UBOT("faudio")
async def fake_audio(client, message: Message):
    await send_fake_action(client, message, enums.ChatAction.RECORD_AUDIO)


@PY.UBOT("fvideo")
async def fake_video(client, message: Message):
    await send_fake_action(client, message, enums.ChatAction.RECORD_VIDEO)


@PY.UBOT("fround")
async def fake_round(client, message: Message):
    await send_fake_action(client, message, enums.ChatAction.RECORD_VIDEO_NOTE)


@PY.UBOT("fphoto")
async def fake_photo(client, message: Message):
    await send_fake_action(client, message, enums.ChatAction.UPLOAD_PHOTO)


@PY.UBOT("fsticker")
async def fake_sticker(client, message: Message):
    await send_fake_action(client, message, enums.ChatAction.CHOOSE_STICKER)


@PY.UBOT("fcontact")
async def fake_contact(client, message: Message):
    await send_fake_action(client, message, enums.ChatAction.CHOOSE_CONTACT)


@PY.UBOT("flocation")
async def fake_location(client, message: Message):
    await send_fake_action(client, message, enums.ChatAction.FIND_LOCATION)


@PY.UBOT("fdocument")
async def fake_document(client, message: Message):
    await send_fake_action(client, message, enums.ChatAction.UPLOAD_DOCUMENT)


@PY.UBOT("fstop")
async def fake_stop(client, message: Message):
    await send_fake_action(client, message, enums.ChatAction.CANCEL)


@PY.UBOT("fscreenshot")
async def fake_screenshot(client, message: Message):
    try:
        jumlah = int(message.command[1]) if len(message.command) > 1 else 1
        if jumlah > 5:
            jumlah = 5
    except ValueError:
        jumlah = 1

    await message.delete()

    for _ in range(jumlah):
        await client.send(
            functions.messages.SendScreenshotNotification(
                peer=await client.resolve_peer(message.chat.id),
                reply_to_msg_id=0,
                random_id=client.rnd_id(),
            )
        )
        await sleep(0.1)
