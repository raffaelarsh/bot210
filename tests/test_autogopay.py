import asyncio
from datetime import timedelta

import pytest

from conftest import FAKE_BOT, STATE, FAKE_DB, utcnow


def run(coro):
    return asyncio.run(coro)


def trx_col():
    return FAKE_DB["autogopay_trx"]


def find_trx(tx):
    return next(d for d in trx_col().docs if d["_id"] == tx)


def premium_list():
    return STATE["vars"].get((999, "PREM_USERS"), [])


def expires_within(dt, expected, seconds=60):
    return abs((dt - expected).total_seconds()) <= seconds


def test_bayar_sukses(env):
    ag, gw = env.ag, env.gw

    async def scenario():
        doc = await ag.create_qris(10, 7)
        gw.status[doc["_id"]] = "settlement"
        await ag.poll_once()
        return doc["_id"]

    tx = run(scenario())
    assert find_trx(tx)["status"] == "paid"
    assert 10 in premium_list()
    assert expires_within(STATE["expiry"][10], utcnow() + timedelta(days=7))
    assert any(chat == 10 for chat, _, _ in FAKE_BOT.sent)  # notif user
    assert any(chat == 1 for chat, _, _ in FAKE_BOT.sent)  # notif owner


def test_klaim_ganda_tidak_aktivasi_dua_kali(env):
    ag, gw = env.ag, env.gw

    async def scenario():
        doc = await ag.create_qris(10, 7)
        gw.status[doc["_id"]] = "settlement"
        results = await asyncio.gather(ag._process_paid(doc), ag._process_paid(doc))
        return results

    results = run(scenario())
    assert sorted(results) == [False, True]
    assert STATE["set_calls"] == [10]
    assert premium_list().count(10) == 1


def test_perpanjangan_dari_sisa_masa_aktif(env):
    ag, gw = env.ag, env.gw
    STATE["expiry"][10] = utcnow() + timedelta(days=3)

    async def scenario():
        doc = await ag.create_qris(10, 7)
        gw.status[doc["_id"]] = "settlement"
        await ag.poll_once()

    run(scenario())
    assert expires_within(STATE["expiry"][10], utcnow() + timedelta(days=10))


def test_expired_dibatalkan_dan_notif(env):
    ag, gw = env.ag, env.gw

    async def scenario():
        doc = await ag.create_qris(10, 7)
        trx_col().docs[0]["expires_at"] = utcnow() - timedelta(minutes=1)
        await ag.poll_once()
        return doc["_id"]

    tx = run(scenario())
    assert find_trx(tx)["status"] == "expired"
    assert "/qris/cancel" in gw.paths()
    assert 10 not in premium_list()
    last_markup = [m for chat, _, m in FAKE_BOT.sent if chat == 10][-1]
    assert last_markup.inline_keyboard[0][0].callback_data == "bayar_dulu"


def test_settlement_tepat_di_batas_waktu_dianggap_sukses(env):
    ag, gw = env.ag, env.gw

    async def scenario():
        doc = await ag.create_qris(10, 7)
        trx_col().docs[0]["expires_at"] = utcnow() - timedelta(seconds=1)
        gw.status[doc["_id"]] = "settlement"
        await ag.poll_once()
        return doc["_id"]

    tx = run(scenario())
    assert find_trx(tx)["status"] == "paid"
    assert "/qris/cancel" not in gw.paths()


def test_batal_oleh_user(env):
    ag, gw = env.ag, env.gw

    async def scenario():
        doc = await ag.create_qris(10, 7)
        state, trx = await ag.cancel_pending(10)
        return state, trx["_id"], doc["_id"]

    state, tx, _ = run(scenario())
    assert state == "cancelled"
    assert find_trx(tx)["status"] == "cancelled"
    assert "/qris/cancel" in gw.paths()
    assert 10 not in premium_list()


def test_batal_setelah_sudah_bayar_diproses_sukses(env):
    ag, gw = env.ag, env.gw

    async def scenario():
        doc = await ag.create_qris(10, 7)
        gw.status[doc["_id"]] = "settlement"
        state, _ = await ag.cancel_pending(10)
        return state, doc["_id"]

    state, tx = run(scenario())
    assert state == "paid"
    assert find_trx(tx)["status"] == "paid"
    assert 10 in premium_list()
    assert "/qris/cancel" not in gw.paths()


def test_dua_qris_beruntun_hanya_satu_pending(env):
    ag = env.ag

    async def scenario():
        await ag.create_qris(10, 7)
        await ag.create_qris(10, 14)

    run(scenario())
    pending = [d for d in trx_col().docs if d["status"] == "pending"]
    assert len(pending) == 1
    assert pending[0]["days"] == 14
    assert sum(1 for d in trx_col().docs if d["status"] == "cancelled") == 1


def test_recovery_status_processing(env):
    ag = env.ag
    now = utcnow()
    trx_col().docs.append(
        {
            "_id": "TXSTUCK",
            "user_id": 10,
            "days": 7,
            "amount": 3000,
            "qr_url": "x",
            "status": "processing",
            "chat_id": None,
            "message_id": None,
            "created_at": now,
            "expires_at": now + timedelta(minutes=10),
            "claimed_at": now - timedelta(seconds=120),
            "new_expire": now + timedelta(days=7),
        }
    )

    run(ag.poll_once())
    run(ag.poll_once())  # siklus kedua tidak boleh mengaktifkan lagi

    assert find_trx("TXSTUCK")["status"] == "paid"
    assert STATE["set_calls"] == [10]
    assert premium_list().count(10) == 1
    assert expires_within(STATE["expiry"][10], now + timedelta(days=7), seconds=5)


def test_api_key_kosong(env, monkeypatch):
    ag, gw = env.ag, env.gw
    monkeypatch.setattr(ag, "AUTOGOPAY_API_KEY", "")
    with pytest.raises(ag.AutoGoPayError) as exc:
        run(ag.create_qris(10, 7))
    assert "AUTOGOPAY_API_KEY" in str(exc.value)
    assert gw.calls == []


def test_paket_tidak_valid(env):
    with pytest.raises(env.ag.AutoGoPayError):
        run(env.ag.create_qris(10, 5))


def test_gangguan_jaringan_diabaikan_lalu_dicoba_lagi(env):
    ag, gw = env.ag, env.gw

    async def scenario():
        doc = await ag.create_qris(10, 7)
        gw.network_down = True
        await ag.poll_once()  # tidak boleh melempar error
        assert find_trx(doc["_id"])["status"] == "pending"
        gw.network_down = False
        gw.status[doc["_id"]] = "settlement"
        await ag.poll_once()
        return doc["_id"]

    tx = run(scenario())
    assert find_trx(tx)["status"] == "paid"
