import asyncio
from datetime import timedelta

import pytest

from conftest import FAKE_BOT, FAKE_DB, FAKE_UBOT, GROUPS, STATE, FakeUbotClient, utcnow


def run(coro):
    return asyncio.run(coro)


def trials():
    return FAKE_DB["trial_users"]


def trial_doc(uid):
    return next(d for d in trials().docs if d["user_id"] == uid)


def join_all(uid, status="MEMBER"):
    for g in GROUPS:
        FAKE_BOT.members[(g, uid)] = status


def premium_list():
    return STATE["vars"].get((999, "PREM_USERS"), [])


def test_join_tiga_grup_lalu_aktif(env):
    t = env.trial
    join_all(10)

    async def scenario():
        assert await t.trial_missing_groups(10) == []
        return await t.trial_activate(10)

    doc = run(scenario())
    assert doc["status"] == "active"
    assert 10 in premium_list()
    assert STATE["expiry"][10] is not None
    expected = utcnow() + timedelta(days=5)
    assert abs((STATE["expiry"][10] - expected).total_seconds()) < 60


def test_kurang_join_menyebut_grup_yang_kurang(env):
    t = env.trial
    join_all(10)
    FAKE_BOT.members[(GROUPS[2], 10)] = "LEFT"  # status keluar dianggap belum join

    assert run(t.trial_missing_groups(10)) == [3]


def test_belum_join_sama_sekali(env):
    assert run(env.trial.trial_missing_groups(10)) == [1, 2, 3]


def test_trial_kedua_ditolak(env):
    t = env.trial
    join_all(10)

    async def scenario():
        await t.trial_activate(10)
        with pytest.raises(t.TrialError):
            await t.trial_activate(10)

    run(scenario())
    assert len(trials().docs) == 1


def test_broadcast_hanya_setelah_6_jam(env, monkeypatch):
    t = env.trial
    join_all(10)
    run(t.trial_activate(10))
    client = FakeUbotClient(10)
    FAKE_UBOT._ubot.append(client)

    run(t._tick())
    assert client.sent == GROUPS  # kirim pertama ke ketiga grup

    run(t._tick())
    assert client.sent == GROUPS  # belum 6 jam: tidak kirim

    last = trial_doc(10)["last_broadcast_at"]
    monkeypatch.setattr(t, "_utcnow", lambda: last + timedelta(hours=5))
    run(t._tick())
    assert len(client.sent) == 3

    monkeypatch.setattr(t, "_utcnow", lambda: last + timedelta(hours=6, minutes=1))
    run(t._tick())
    assert len(client.sent) == 6


def test_trial_habis_logout_otomatis(env, monkeypatch):
    t = env.trial
    join_all(10)
    run(t.trial_activate(10))
    client = FakeUbotClient(10)
    FAKE_UBOT._ubot.append(client)
    FAKE_UBOT._get_my_id.append(10)
    end = trial_doc(10)["trial_expires_at"] + timedelta(minutes=1)
    monkeypatch.setattr(t, "_utcnow", lambda: end)

    run(t._tick())

    assert trial_doc(10)["status"] == "expired"
    assert client.logged_out
    assert client not in FAKE_UBOT._ubot
    assert 10 not in FAKE_UBOT._get_my_id
    assert 10 in STATE["db_ubot_removed"]
    assert 10 not in premium_list()
    assert any(chat == 10 for chat, _, _ in FAKE_BOT.sent)

    run(t._tick())  # tidak diproses dua kali
    assert len([c for c in FAKE_BOT.sent if c[0] == 10]) == 1


def test_user_berbayar_setelah_trial_habis_tetap_premium(env, monkeypatch):
    t = env.trial
    join_all(10)
    run(t.trial_activate(10))
    trial_end = trial_doc(10)["trial_expires_at"]
    STATE["expiry"][10] = trial_end + timedelta(days=7)
    monkeypatch.setattr(t, "_utcnow", lambda: trial_end + timedelta(minutes=1))
    run(t._tick())  # trial berakhir, user sudah bayar

    assert run(t.trial_is_paid_premium(10)) is True
    with pytest.raises(t.TrialError):
        run(t.trial_activate(10))  # trial tetap tidak bisa diulang


def test_premium_berbayar_tidak_ikut_logout(env, monkeypatch):
    t = env.trial
    join_all(10)
    run(t.trial_activate(10))
    client = FakeUbotClient(10)
    FAKE_UBOT._ubot.append(client)
    trial_end = trial_doc(10)["trial_expires_at"]
    # simulasi: user sudah membayar paket 7 hari di tengah trial
    STATE["expiry"][10] = trial_end + timedelta(days=7)
    monkeypatch.setattr(t, "_utcnow", lambda: trial_end + timedelta(minutes=1))

    run(t._tick())

    assert trial_doc(10)["status"] == "expired"
    assert not client.logged_out
    assert client in FAKE_UBOT._ubot
    assert 10 in premium_list()
    assert 10 not in STATE["db_ubot_removed"]
