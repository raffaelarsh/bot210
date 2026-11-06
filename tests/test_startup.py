import asyncio

from conftest import FAKE_BOT, plugins


def test_notifikasi_startup_gagal_tidak_mematikan(monkeypatch, capsys):
    async def boom(*args, **kwargs):
        raise RuntimeError("PeerIdInvalid")

    monkeypatch.setattr(FAKE_BOT, "send_message", boom)
    asyncio.run(plugins.loadPlugins())
    out = capsys.readouterr().out
    assert "[WARN]" in out
    assert "PeerIdInvalid" in out


def test_notifikasi_startup_normal(monkeypatch):
    calls = []

    async def ok(chat_id, text, **kwargs):
        calls.append(chat_id)

    monkeypatch.setattr(FAKE_BOT, "send_message", ok)
    asyncio.run(plugins.loadPlugins())
    assert calls == [1]  # OWNER_ID pada stub config
