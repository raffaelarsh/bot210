from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from PyroUbot import OWNER_ID, PREMIUM_PLANS, bot, ubot, get_expired_date
from PyroUbot.core.format_util import format_rupiah


class MSG:     
    def EXP_MSG_UBOT(X):
        return f"""
<blockquote><b>❏ ᴘᴇᴍʙᴇʀɪᴛᴀʜᴜᴀɴ</b>
<b>├ ᴀᴋᴜɴ:</b> <a href=tg://user?id={X.me.id}>{X.me.first_name} {X.me.last_name or ''}</a>
<b>├ ɪᴅ:</b> <code>{X.me.id}</code>
<b>╰ ᴍᴀsᴀ ᴀᴋᴛɪꜰ ᴛᴇʟᴀʜ ʜᴀʙɪs</b></blockquote>
"""

    def START(message):
        return f"""
<blockquote><b>👋🏻 ʜᴀʟᴏ <a href=tg://user?id={message.from_user.id}>{message.from_user.first_name} {message.from_user.last_name or ''}</a>!

<b> 📚💎@{bot.me.username} ᴀᴅᴀʟᴀʜ ʙᴏᴛ ʏᴀɴɢ ᴅᴀᴘᴀᴛ ᴍᴇᴍʙᴜᴀᴛ ᴜsᴇʀʙᴏᴛ ᴅᴇɴɢᴀɴ ᴍᴜᴅᴀʜ</b>

🚀ʙᴏᴛ ɪɴɪ ᴅɪᴋᴇᴍʙᴀɴɢᴋᴀɴ ᴏʟᴇʜ <a href=tg://openmessage?user_id={OWNER_ID}>@anyonima</a> ᴊɪᴋᴀ ᴀᴅᴀ ᴋᴇsᴀʟᴀʜᴀɴ ᴀᴛᴀᴜᴘᴜɴ ᴍᴀsᴀʟᴀʜ ᴅᴍ ᴏᴡɴᴇʀ ʙᴏᴛ 𝙳𝙸 𝙰𝚃𝙰𝚂 


𝙲𝙰𝚁𝙰 𝚂𝙴𝚆𝙰 𝚄𝚂𝙴𝚁𝙱𝙾𝚃:
(ᴜꜱᴇʀʙᴏᴛ ɪɴɪ ᴀᴋᴀɴ ʙᴇʀᴋᴇᴍʙᴀɴɢ!! ᴊɪᴋᴀ ɪɴɢɪɴ ᴍᴇᴍʙᴇʟɪ ᴜꜱᴇʀʙᴏᴛ ᴀᴛᴀᴜ ʀᴇꜱᴇʟʟᴇʀ ʙɪꜱᴀ ᴄʜᴀᴛ ᴏᴡɴᴇʀ ᴜᴛᴀᴍᴀ ᴋᴀʀɴᴀ ᴜꜱᴇʀʙᴏᴛ ɪɴɪ ʙᴇʟᴜᴍ ꜱᴜᴘᴘᴏʀᴛ ᴛʀᴀɴꜱᴀᴋꜱɪ ᴏᴛᴏᴍᴀᴛɪꜱ!!!, ᴊɪᴋᴀ ᴀᴅᴀ ᴋᴇɴᴅᴀʟᴀ ꜰɪᴛᴜʀ ᴇʀᴏʀ ʙɪꜱᴀ ᴄʜᴀᴛ ᴏᴡɴᴇʀ ᴜᴛᴀᴍᴀ ᴀɢᴀʀ ᴅɪ ᴘᴇʀʙᴀɪᴋɪ)

ᴋʟɪᴋ ᴛᴏᴍʙᴏʟ ᴅɪʙᴀᴡᴀʜ ᴜɴᴛᴜᴋ ᴍᴇᴍʙᴜᴀᴛ ᴜsᴇʀʙᴏᴛ</b></blockquote>
"""

    def TEXT_PAYMENT(days, harga):
        paket = "\n".join(
            f"<b>├ {d} ʜᴀʀɪ: {format_rupiah(p)}</b>" for d, p in sorted(PREMIUM_PLANS.items())
        )
        return f"""
<blockquote><b>💬 sɪʟᴀʜᴋᴀɴ ᴘɪʟɪʜ ᴘᴀᴋᴇᴛ ᴅᴀɴ ᴍᴇᴛᴏᴅᴇ ᴘᴇᴍʙᴀʏᴀʀᴀɴ</b>

<b>📦 ᴘᴀᴋᴇᴛ ᴅɪᴘɪʟɪʜ: {days} ʜᴀʀɪ</b>
<b>🔖 ᴛᴏᴛᴀʟ ʜᴀʀɢᴀ: {format_rupiah(harga)}</b>

<b>🏷 ᴅᴀꜰᴛᴀʀ ᴘᴀᴋᴇᴛ:</b>
{paket}

<b>💳 ᴍᴇᴛᴏᴅᴇ ᴘᴇᴍʙᴀʏᴀʀᴀɴ:</b>
<b>├ ⚡ ǫʀɪs ᴏᴛᴏᴍᴀᴛɪs</b> (ᴋᴏɴꜰɪʀᴍᴀsɪ ᴏᴛᴏᴍᴀᴛɪꜱ ꜱᴇᴛᴇʟᴀʜ ʙᴀʏᴀʀ)
<b>╰ ᴍᴀɴᴜᴀʟ</b> (ᴋɪʀɪᴍ ʙᴜᴋᴛɪ ᴋᴇ ᴏᴡɴᴇʀ ᴊɪᴋᴀ ǫʀɪs ᴛɪᴅᴀᴋ ʙɪsᴀ)

OWNER BOT : <a href=tg://openmessage?user_id={OWNER_ID}>@anyonima</a>

<b>🛍 ᴋʟɪᴋ ᴛᴏᴍʙᴏʟ ᴜɴᴛᴜᴋ ᴍᴇʟᴀɴᴊᴜᴛᴋᴀɴ ᴘᴇᴍʙᴀʏᴀʀᴀɴ</b></blockquote>
"""

    async def UBOT(count):
        return f"""
<blockquote><b>╭〢 ᴛʜʀᴇᴇʙᴏᴛ ᴋᴇ </b> <code>{int(count) + 1}/{len(ubot._ubot)}</code>
<b> ├〢 ᴀᴄᴄᴏᴜɴᴛ </b> <a href=tg://user?id={ubot._ubot[int(count)].me.id}>{ubot._ubot[int(count)].me.first_name} {ubot._ubot[int(count)].me.last_name or ''}</a> 
<b> ╰〢ᴜsᴇʀ ɪᴅ </b> <code>{ubot._ubot[int(count)].me.id}</code></blockquote>
"""

    def POLICY():
        return """ <blockquote><b>ᴊɪᴋᴀ ᴀᴅᴀ ᴋᴇɴᴅᴀʟᴀ sɪʟᴀʜᴋᴀɴ ʜᴜʙᴜɴɢɪ  <a href=tg://openmessage?user_id={OWNER_ID}>@anyonima</a></b></blockquote>
"""
