import secrets

import requests

KLDSCP_SUPPORTED_ORIGINS = [
    "amnezia.org",
    "doxa.team",
    "holod.media",
    "memorialcenter.org",
    "nvpn.work",
    "regaspect.info",
    "semnasem.org",
    "theins.ru",
    "thenewtab.io",
    "zaodno.org",
]

fingerprint = secrets.token_hex(16)


def get_kaleidoscope_mirror(origin: str) -> str | None:
    if origin not in KLDSCP_SUPPORTED_ORIGINS:
        return None
    payload = {"fingerprint": fingerprint, "hostname": origin}
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) Gecko/20100101 Firefox/148.0",
        "Accept": "application/json",
        "Accept-Language": "en-GB,en;q=0.9",
        "Content-Type": "application/json",
        "Referer": "https://storage.googleapis.com/",
        "Origin": "https://storage.googleapis.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Priority": "u=4",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers",
    }
    response = requests.post(
        "https://kldscpe.info/api/v2/resolve", json=payload, headers=headers
    )
    if response.status_code == 200:
        try:
            return response.json()["upstream"]
        except KeyError:
            return None
    return None
