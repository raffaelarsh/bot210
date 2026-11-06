"""Tes tanpa menjalankan bot: pyrogram dan modul database distub, sedangkan
autogopay.py dan trial.py dimuat dari file aslinya."""

import importlib.util
import os
import sys
import types
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "PyroUbot")


def _stub(name, **attrs):
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    sys.modules[name] = mod
    return mod


# ── stub pyrogram ─────────────────────────────────────────────────
class InlineKeyboardButton(SimpleNamespace):
    def __init__(self, text, callback_data=None, url=None):
        super().__init__(text=text, callback_data=callback_data, url=url)


class InlineKeyboardMarkup(SimpleNamespace):
    def __init__(self, inline_keyboard):
        super().__init__(inline_keyboard=inline_keyboard)


class RPCError(Exception):
    pass


class FloodWait(RPCError):
    def __init__(self, value=0):
        super().__init__(value)
        self.value = value


class UserNotParticipant(RPCError):
    pass


class MessageNotModified(RPCError):
    pass


_stub("pyrogram", __version__="test")
_stub(
    "pyrogram.types",
    InlineKeyboardButton=InlineKeyboardButton,
    InlineKeyboardMarkup=InlineKeyboardMarkup,
)
_stub(
    "pyrogram.errors",
    RPCError=RPCError,
    FloodWait=FloodWait,
    UserNotParticipant=UserNotParticipant,
    MessageNotModified=MessageNotModified,
)


# ── fake Mongo ────────────────────────────────────────────────────
class FakeResult:
    def __init__(self, modified_count=0, upserted_id=None):
        self.modified_count = modified_count
        self.upserted_id = upserted_id


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    async def to_list(self, length=None):
        return [dict(d) for d in self._docs]


def _match(doc, flt):
    for key, cond in (flt or {}).items():
        val = doc.get(key)
        if isinstance(cond, dict) and cond and all(k.startswith("$") for k in cond):
            for op, arg in cond.items():
                if op == "$lt" and not (val is not None and val < arg):
                    return False
                if op == "$gte" and not (val is not None and val >= arg):
                    return False
                if op == "$exists" and (key in doc) != bool(arg):
                    return False
        elif val != cond:
            return False
    return True


def _apply(doc, upd):
    for op, fields in upd.items():
        if op == "$set":
            doc.update(fields)
        elif op == "$unset":
            for k in fields:
                doc.pop(k, None)


class FakeCol:
    def __init__(self):
        self.docs = []

    async def find_one(self, flt=None):
        for d in self.docs:
            if _match(d, flt):
                return dict(d)
        return None

    def find(self, flt=None):
        return FakeCursor([d for d in self.docs if _match(d, flt)])

    async def insert_one(self, doc):
        if any(d["_id"] == doc["_id"] for d in self.docs):
            raise RuntimeError("duplicate _id")
        self.docs.append(dict(doc))

    async def update_one(self, flt, upd, upsert=False):
        for d in self.docs:
            if _match(d, flt):
                before = dict(d)
                _apply(d, upd)
                return FakeResult(modified_count=int(d != before))
        if upsert:
            new = {k: v for k, v in (flt or {}).items() if not isinstance(v, dict)}
            new.update(upd.get("$setOnInsert", {}))
            _apply(new, {k: v for k, v in upd.items() if k != "$setOnInsert"})
            new.setdefault("_id", f"auto-{len(self.docs)}")
            self.docs.append(new)
            return FakeResult(upserted_id=new["_id"])
        return FakeResult()

    async def find_one_and_update(self, flt, upd, return_document=None):
        for d in self.docs:
            if _match(d, flt):
                _apply(d, upd)
                return dict(d)
        return None

    async def create_index(self, *args, **kwargs):
        return "ok"


class FakeDB:
    def __init__(self):
        self._cols = {}

    def __getitem__(self, name):
        return self._cols.setdefault(name, FakeCol())


FAKE_DB = FakeDB()
ReturnDocument = SimpleNamespace(AFTER=True)


# ── state fake untuk fungsi database ──────────────────────────────
STATE = {}


def reset_state():
    STATE.clear()
    STATE.update(
        expiry={},  # user_id -> datetime naive UTC
        vars={},  # (owner_id, name) -> list
        set_calls=[],  # user_id per set_expired_date
        removed_vars=[],
        db_ubot_removed=[],
    )


def _to_naive_utc(dt):
    if dt is None or dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


async def get_expired_date(user_id):
    return STATE["expiry"].get(user_id)


async def set_expired_date(user_id, expire_date):
    STATE["expiry"][user_id] = _to_naive_utc(expire_date)
    STATE["set_calls"].append(user_id)


async def rem_expired_date(user_id):
    STATE["expiry"].pop(user_id, None)


async def get_list_from_vars(owner_id, name):
    return list(STATE["vars"].get((owner_id, name), []))


async def add_to_vars(owner_id, name, value):
    STATE["vars"].setdefault((owner_id, name), []).append(value)


async def remove_from_vars(owner_id, name, value):
    lst = STATE["vars"].get((owner_id, name), [])
    if value in lst:
        lst.remove(value)


async def remove_all_vars(user_id):
    STATE["removed_vars"].append(user_id)


async def remove_ubot(user_id):
    STATE["db_ubot_removed"].append(user_id)


# ── stub modul PyroUbot ───────────────────────────────────────────
class FakeBot:
    def __init__(self):
        self.me = SimpleNamespace(id=999, username="fakebot", mention="@fakebot")
        self.reset()

    def reset(self):
        self.sent = []  # (chat_id, text, reply_markup)
        self.deleted = []
        self.members = {}  # (chat_id, user_id) -> "MEMBER" | "LEFT"

    async def send_message(self, chat_id, text, reply_markup=None, **kwargs):
        self.sent.append((chat_id, text, reply_markup))
        return SimpleNamespace(id=len(self.sent))

    async def delete_messages(self, chat_id, message_id):
        self.deleted.append((chat_id, message_id))

    async def get_chat_member(self, chat_id, user_id):
        status = self.members.get((chat_id, user_id))
        if status is None:
            raise UserNotParticipant("not participant")
        return SimpleNamespace(status=SimpleNamespace(name=status))


class FakeUbotClient:
    def __init__(self, user_id):
        self.me = SimpleNamespace(id=user_id, first_name="u", last_name="")
        self.sent = []
        self.logged_out = False

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append(chat_id)

    async def unblock_user(self, username):
        return True

    async def log_out(self):
        self.logged_out = True


FAKE_BOT = FakeBot()
FAKE_UBOT = SimpleNamespace(_ubot=[], _get_my_id=[])

GROUPS = [-1002173432931, -1002414865406, -1002370541540]

_pkg = _stub("PyroUbot", bot=FAKE_BOT, ubot=FAKE_UBOT)
_stub(
    "PyroUbot.config",
    AUTOGOPAY_API_KEY="test-key",
    AUTOGOPAY_BASE_URL="https://gw.test",
    QRIS_EXPIRE_MINUTES=10,
    QRIS_POLL_INTERVAL=6,
    PREMIUM_PLANS={7: 3000, 14: 5000, 30: 10000},
    OWNER_ID=1,
    GROUP_TRIAL_IDS=GROUPS,
    TRIAL_GROUP_LINKS=["https://t.me/+a", "https://t.me/+b", "https://t.me/+c"],
    TRIAL_DAYS=5,
    TRIAL_BROADCAST_HOURS=6,
)
_stub("PyroUbot.core")


class _PY:
    @staticmethod
    def CALLBACK(name):
        def deco(fn):
            return fn

        return deco


_stub("PyroUbot.core.helpers", PY=_PY())
_stub("PyroUbot.modules", loadModule=lambda: [])
_stub("PyroUbot.core.database", mongodb=FAKE_DB)
_stub(
    "PyroUbot.core.database.expired",
    get_expired_date=get_expired_date,
    set_expired_date=set_expired_date,
    rem_expired_date=rem_expired_date,
)
_stub(
    "PyroUbot.core.database.variabel",
    add_to_vars=add_to_vars,
    get_list_from_vars=get_list_from_vars,
    remove_from_vars=remove_from_vars,
    remove_all_vars=remove_all_vars,
)
_stub("PyroUbot.core.database.userbot", remove_ubot=remove_ubot)


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PKG, relpath))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


format_util = _load("PyroUbot.core.format_util", os.path.join("core", "format_util.py"))
setattr(sys.modules["PyroUbot.core"], "format_util", format_util)
autogopay = _load("PyroUbot.core.function.autogopay", os.path.join("core", "function", "autogopay.py"))
trial = _load("PyroUbot.core.function.trial", os.path.join("core", "function", "trial.py"))
plugins = _load("PyroUbot.core.function.plugins", os.path.join("core", "function", "plugins.py"))


class Gateway:
    """Pengganti _post: meniru API AutoGoPay dalam memori."""

    def __init__(self):
        self.status = {}
        self.calls = []
        self.counter = 0
        self.network_down = False

    async def post(self, path, body):
        import httpx

        self.calls.append((path, body))
        if self.network_down:
            raise httpx.ConnectError("down")
        if path == "/qris/generate":
            self.counter += 1
            tx = f"TX{self.counter}"
            self.status[tx] = "pending"
            return {
                "success": True,
                "data": {"transaction_id": tx, "amount": body["amount"], "qr_url": f"https://qr.test/{tx}.png"},
            }
        if path == "/qris/status":
            tx = body["transaction_id"]
            return {"success": True, "data": {"transaction_status": self.status.get(tx, "pending")}}
        if path == "/qris/cancel":
            tx = body["transaction_id"]
            self.status[tx] = "cancel"
            return {"success": True, "data": {}}
        return {"success": False}

    def paths(self):
        return [p for p, _ in self.calls]


@pytest.fixture(autouse=True)
def env(monkeypatch):
    reset_state()
    for col in FAKE_DB._cols.values():  # modul menyimpan referensi koleksi, jadi kosongkan isinya
        col.docs.clear()
    FAKE_BOT.reset()
    FAKE_UBOT._ubot.clear()
    FAKE_UBOT._get_my_id.clear()
    gw = Gateway()
    monkeypatch.setattr(autogopay, "_post", gw.post)
    monkeypatch.setattr(autogopay, "AUTOGOPAY_API_KEY", "test-key")

    async def _nosleep(*a, **k):
        return None

    # hanya modul trial yang memakai sleep tiruan (jeda antar grup)
    monkeypatch.setattr(
        trial, "asyncio", SimpleNamespace(sleep=_nosleep, Lock=trial.asyncio.Lock)
    )
    return SimpleNamespace(ag=autogopay, trial=trial, gw=gw, bot=FAKE_BOT, ubot=FAKE_UBOT)


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)
