import logging

import requests

from src.database import get_db_session
from src.mirrors.service import refresh_mirrors
from src.utils import repeat_every


@repeat_every(seconds=600)
def update_rsf_mirrors():
        try:
            r = requests.get(
                "https://raw.githubusercontent.com/RSF-RWB/collateralfreedom/refs/heads/main/sites.json",
                timeout = 30,
            )
            r.raise_for_status()
            mirrors = r.json()
        except (requests.RequestException, ValueError) as e:
            logging.exception(e)
            return
        with get_db_session() as db:
            refresh_mirrors(db, -2, mirrors)  # Tracking as hardcoded pool -2
            db.commit()