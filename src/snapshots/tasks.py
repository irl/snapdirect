import logging
from datetime import datetime

from src.database import get_db_session
from src.snapshots.client import SnapshotCamera
from src.snapshots.models import Snapshot, SnapshotState
from src.google.client import upload_blob
from src.utils import hashids


def generate_snapshot(id_: int) -> None:
    with get_db_session() as db:
        snapshot = (
            db.query(Snapshot)
            .filter(Snapshot.id == id_, Snapshot.snapshot_state == SnapshotState.PENDING)
            .first()
        )
        if not snapshot:
            return
        try:
            content = SnapshotCamera(snapshot.url).render()
            upload_blob(hashids.encode(snapshot.id) + ".html", content.encode("utf-8"), "text/html")
            snapshot.snapshot_state = SnapshotState.UPDATING
            snapshot.snapshot_published_at = datetime.now()
            db.commit()
        except Exception as e:
            logging.error(e)
            snapshot.snapshot_state = SnapshotState.FAILED
            db.commit()
