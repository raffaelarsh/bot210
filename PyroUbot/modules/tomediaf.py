import aiohttp
import filetype
from io import BytesIO
from PyroUbot import *

__MODULE__ = "ᴛᴏ ᴍᴇᴅɪᴀғɪʀᴇ"
__HELP__ = """
<blockquote><b>Bantuan untuk To Mediafire

perintah : <code>{0}tomediaf</code> [reply file]
    mengapload file ke Link Mediafire</b></blockquote>
"""

async def upload_file(buffer: BytesIO) -> str:
    kind = filetype.guess(buffer)
    if kind is None:
        raise ValueError("Cannot determine file type")
    ext = kind.extension

    buffer.seek(0)
    form = aiohttp.FormData()
    form.add_field(
        'fileToUpload',
        buffer,
        filename='file.' + ext,
        content_type=kind.mime
    )
    form.add_field('reqtype', 'fileupload')

    async with aiohttp.ClientSession() as session:
        async with session.post('https://www.mediafire.com/api/1.5/file/upload.php', data=form) as response:
            if response.status != 200:
                raise Exception(f"Failed to upload file: {response.status}")
            return await response.text()

@PY.UBOT("tomediaf|tm")
async def _(client, message):
    reply_message = message.reply_to_message
    if reply_message and reply_message.media:
        downloaded_file = await reply_message.download()
        
        with open(downloaded_file, 'rb') as f:
            buffer = BytesIO(f.read())
            try:
                media_url = await upload_file(buffer)
                await message.reply(f"<b>berhasil diupload ke mediafire : <a href='{media_url}'>LINK NYA KINGZ</a></b>")
            except Exception as e:
                await message.reply(f"Error: {e}")
    else:
        await message.reply("Mana File Nya Bjirtt")
