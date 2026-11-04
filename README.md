# PyroUbot

## Clone

```bash
git clone https://github.com/raffaelarsh/bot210
cd bot210
```

## Install

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3.10-venv python3-pip
python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Config

Buat file `.env` di root project dan isi:

```env
API_ID=
API_HASH=
BOT_TOKEN=
OWNER_ID=
MONGO_URL=
DEVS=
BLACKLIST_CHAT=
RMBG_API=
LOGS_MAKER_UBOT=
MAX_BOT=999
```

## Run

```bash
python3 -m PyroUbot
```

## Update

```bash
git pull origin main
```
