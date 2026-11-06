import os
from dotenv import load_dotenv

load_dotenv(".env")

MAX_BOT = int(os.getenv("MAX_BOT", "999"))

DEVS = list(map(int, os.getenv("DEVS", "7520490068").split()))

API_ID = int(os.getenv("API_ID", "0"))

API_HASH = os.getenv("API_HASH", "")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

OWNER_ID = int(os.getenv("OWNER_ID", "7520490068"))

BLACKLIST_CHAT = list(map(int, os.getenv("BLACKLIST_CHAT", "-1002886184276").split()))

RMBG_API = os.getenv("RMBG_API", "")

MONGO_URL = os.getenv("MONGO_URL", "")

LOGS_MAKER_UBOT = int(os.getenv("LOGS_MAKER_UBOT", "-1002671518601"))

# ── AutoGoPay (pembayaran QRIS otomatis) ──────────────────────────
AUTOGOPAY_API_KEY = os.getenv("AUTOGOPAY_API_KEY", "")
AUTOGOPAY_BASE_URL = os.getenv("AUTOGOPAY_BASE_URL", "https://v1-gateway.autogopay.site")
QRIS_EXPIRE_MINUTES = int(os.getenv("QRIS_EXPIRE_MINUTES", "10"))
QRIS_POLL_INTERVAL = int(os.getenv("QRIS_POLL_INTERVAL", "6"))
QRIS_CANCEL_COOLDOWN_MINUTES = int(os.getenv("QRIS_CANCEL_COOLDOWN_MINUTES", "5"))

# Paket premium: key = jumlah hari, value = harga (rupiah)
PREMIUM_PLANS = {7: 3000, 14: 5000, 30: 10000}

# ── Coba trial ────────────────────────────────────────────────────
# chat_id 3 grup wajib dipisah koma, mis. -100111,-100222,-100333
GROUP_TRIAL_IDS = [
    int(x) for x in os.getenv("GROUP_TRIAL_IDS", "").replace(",", " ").split()
]
TRIAL_GROUP_LINKS = [
    "https://t.me/+Lk08j0_KoFc4N2Zl",
    "https://t.me/+2Y_Vst_Ma-4xNjU1",
    "https://t.me/+ozJtAftBy-83MjBl",
]
TRIAL_DAYS = 5
TRIAL_BROADCAST_HOURS = int(os.getenv("TRIAL_BROADCAST_HOURS", "3"))
