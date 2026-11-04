# PyroUbot/modules/enchtml.py

import base64
import random
import string
import asyncio 
import os
import tempfile
from time import time
from PyroUbot import *

__MODULE__ = "ᴇɴᴄʜᴛᴍʟ"

__HELP__ = """
<blockquote>🔐 <b>ENC HTML</b>

<code>{0}enchtml</code>
<b>➥ Reply ke HTML untuk di-encrypt</b>
<b>➥ HTML hanya bisa dibuka via browser</b>
<b>➥ Source tidak bisa dibaca</b></blockquote>
"""
def _rand(n=10):
    return ''.join(random.choice(string.ascii_letters) for _ in range(n))

def _xor(data: bytes, key: bytes):
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

@PY.UBOT("enchtml")
async def enc_html_brutal(client, message):
    reply = message.reply_to_message
    if not reply:
        return await message.reply("❌ Reply ke text atau file HTML.")

    data = None

    # TEXT / CAPTION
    if reply.text or reply.caption:
        data = reply.text or reply.caption

    # FILE HTML
    elif reply.document:
        name = reply.document.file_name or ""
        if not name.lower().endswith((".html", ".htm")):
            return await message.reply("❌ File harus .html atau .htm")

        proc = await message.reply("🔐 Mengunduh file HTML...\n[░░░░░░░░░░] 0%")
        path = await reply.download()

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        finally:
            if os.path.exists(path):
                os.remove(path)

    if not data:
        return await message.reply("❌ Tidak bisa membaca isi HTML.")

    # PROGRESS BAR
    proc = await message.reply("🔐 Encrypting HTML...\n[░░░░░░░░░░] 0%")

    async def bar(p):
        fill = "█" * (p // 10)
        empty = "░" * (10 - len(fill))
        await proc.edit(f"🔐 Encrypting HTML...\n[{fill}{empty}] {p}%")

    await bar(20); await asyncio.sleep(0.2)

    raw = data.encode()
    key = _rand(16).encode()

    await bar(40); await asyncio.sleep(0.2)
    s1 = _xor(raw, key)

    await bar(60); await asyncio.sleep(0.2)
    s2 = base64.b64encode(s1)

    await bar(80); await asyncio.sleep(0.2)
    s3 = base64.b64encode(s2).decode()

    await bar(100); await asyncio.sleep(0.3)

    v1, v2 = _rand(), _rand()

    result_html = f"""<script>
(function(){{
 var {v1}="{s3}";
 var {v2}="{key.decode()}";
 function d(a,k){{
  a=atob(atob(a));
  let r="";
  for(let i=0;i<a.length;i++)r+=String.fromCharCode(a.charCodeAt(i)^k.charCodeAt(i%k.length));
  return r;
 }}
 setInterval(()=>{{if(window.outerHeight-window.innerHeight>200)document.body.innerHTML="";}},400);
 document.write(d({v1},{v2}));
 setTimeout(()=>{{document.currentScript.remove();}},800);
}})();
</script>"""

    filename = f"enc_{int(time())}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(result_html)

    await proc.delete()
    await message.reply_document(
        filename,
        caption="🔥 HTML berhasil dienkripsi"
    )

    os.remove(filename)