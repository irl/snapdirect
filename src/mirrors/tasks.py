import requests

from src.database import get_db_session
from src.mirrors.service import refresh_mirrors
from src.utils import repeat_every


@repeat_every(seconds=600)
def update_rsf_mirrors():
    with get_db_session() as db:
        r = requests.get(
            "https://raw.githubusercontent.com/RSF-RWB/collateralfreedom/refs/heads/main/sites.json"
        )
        mirrors = r.json()
        refresh_mirrors(db, -2, mirrors)  # Tracking as hardcoded pool -2
        db.commit()
