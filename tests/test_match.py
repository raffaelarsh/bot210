"""Tes animasi match dengan pesan dan client palsu (tanpa koneksi Telegram)."""

import asyncio
import importlib.util
import os
import sys
import time
import types
from types import SimpleNamespace

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _stub(name, **attrs):
    if name in sys.modules:
        return sys.modules[name]
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    sys.modules[name] = mod
    return mod


class RPCError(Exception):
    pass


class FloodWait(RPCError):
    def __init__(self, value=0):
        super().__init__(value)
        self.value = value


class MessageNotModified(RPCError):
    pass


async def _get_prefix(_user_id):
    return ["."]


async def _noop(*_args, **_kwargs):
    return None


class _PY:
    @staticmethod
    def UBOT(_name):
        return lambda fn: fn


_stub("pyrogram")
_stub("pyrogram.enums", ParseMode=SimpleNamespace(DISABLED="disabled"))
_stub("pyrogram.errors", RPCError=RPCError, FloodWait=FloodWait, MessageNotModified=MessageNotModified)
_stub(
    "PyroUbot",
    PY=_PY(),
    bot=None,
    ubot=SimpleNamespace(get_prefix=_get_prefix),
    set_vars=_noop,
    get_vars=_noop,
)


def load_match():
    spec = importlib.util.spec_from_file_location(
        "match_under_test", os.path.join(ROOT, "PyroUbot", "modules", "match.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


match = load_match()


def run(coro):
    return asyncio.run(coro)


class FakeMsg:
    """Pesan milik sendiri. Edit memakan `delay` detik; `flood_at` memicu FloodWait
    pada panggilan edit dengan indeks tertentu (dihitung dari 0)."""

    def __init__(self, delay=0.15, flood_at=None):
        self.delay = delay
        self.flood_at = flood_at or {}
        self.calls = 0
        self.edits = []
        self.outgoing = True
        self.from_user = SimpleNamespace(id=1)
        self.chat = SimpleNamespace(id=100)
        self.reply_to_message = None
        self.command = []
        self.replies = []

    async def reply_text(self, text, parse_mode=None):
        self.replies.append(text)

    async def edit(self, text, parse_mode=None):
        idx = self.calls
        self.calls += 1
        await asyncio.sleep(self.delay)
        if idx in self.flood_at:
            raise FloodWait(self.flood_at[idx])
        self.edits.append(text)


class FakeClient:
    def __init__(self):
        self.me = SimpleNamespace(id=1)
        self.stickers = []
        self.messages = []

    async def send_sticker(self, chat_id, file_id):
        self.stickers.append((chat_id, file_id))

    async def send_message(self, chat_id, text, parse_mode=None):
        self.messages.append(text)


@pytest.fixture(autouse=True)
def sticker_tersimpan(monkeypatch):
    async def get_vars(_owner, _var):
        return "FILEID"

    monkeypatch.setattr(match, "get_vars", get_vars)


def play(cmd, msg, client=None):
    client = client or FakeClient()
    var, frames = match.COMMANDS[cmd]
    run(match._play(client, msg, cmd, var, frames, "."))
    return client


def test_frame_dibatasi_dan_unik():
    for cmd, (_var, frames) in match.COMMANDS.items():
        deduped = match._dedupe(frames)
        assert len(deduped) <= match.MAX_FRAMES, cmd
        assert len(deduped) == len(frames), f"{cmd} punya frame identik berurutan"


@pytest.mark.parametrize("cmd", ["m1", "m1only", "m2", "m3"])
def test_total_animasi_kurang_dari_2_detik(cmd):
    msg = FakeMsg(delay=0.15)
    start = time.monotonic()
    client = play(cmd, msg)
    total = time.monotonic() - start

    _var, frames = match.COMMANDS[cmd]
    assert total < 2.0
    assert msg.edits[-1] == match._dedupe(frames)[-1]
    assert client.stickers == [(100, "FILEID")]


def test_lambat_melewati_batas_lompat_ke_frame_akhir():
    msg = FakeMsg(delay=0.5)
    client = play("m1", msg)

    _var, frames = match.COMMANDS["m1"]
    assert msg.edits[-1] == match._dedupe(frames)[-1]
    assert len(msg.edits) < len(frames)
    assert client.stickers == [(100, "FILEID")]


def test_floodwait_pendek_lalu_frame_akhir_dan_sticker():
    msg = FakeMsg(delay=0.05, flood_at={1: 1})
    client = play("m1", msg)

    _var, frames = match.COMMANDS["m1"]
    assert msg.edits[-1] == match._dedupe(frames)[-1]
    assert client.stickers == [(100, "FILEID")]


def test_floodwait_panjang_tanpa_edit_lagi_tapi_sticker_terkirim():
    msg = FakeMsg(delay=0.05, flood_at={1: 10})
    start = time.monotonic()
    client = play("m1", msg)
    total = time.monotonic() - start

    assert total < 2.0  # tidak tidur selama 10 detik
    assert len(msg.edits) == 1  # hanya frame pertama
    assert msg.calls == 2  # tidak ada edit setelah FloodWait
    assert client.stickers == [(100, "FILEID")]


def test_tanpa_sticker_tersimpan_kirim_pesan_bukan_sticker(monkeypatch):
    async def no_sticker(_owner, _var):
        return None

    monkeypatch.setattr(match, "get_vars", no_sticker)
    msg = FakeMsg(delay=0.01)
    client = play("m2", msg)

    assert client.stickers == []
    assert msg.replies and "Belum ada sticker" in msg.replies[0]
