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
