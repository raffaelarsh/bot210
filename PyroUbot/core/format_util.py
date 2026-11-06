"""Format tanggal (WIB) dan rupiah.

Modul leaf: tidak mengimpor PyroUbot agar aman dipakai saat inisialisasi paket
(menghindari circular import).
"""

from datetime import timezone as dt_timezone

import pytz

JAKARTA = pytz.timezone("Asia/Jakarta")


def _to_utc_naive(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt  # Mongo / data naive dianggap UTC
    return dt.astimezone(dt_timezone.utc).replace(tzinfo=None)


def _to_jakarta(dt):
    return pytz.utc.localize(_to_utc_naive(dt)).astimezone(JAKARTA)


def format_wib(dt) -> str:
    return _to_jakarta(dt).strftime("%d-%m-%Y %H:%M")


def format_rupiah(amount: int) -> str:
    return "Rp " + f"{int(amount):,}".replace(",", ".")
