"""Photos des refuges copiées depuis refuges.info."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Refuge, RefugeKind, RefugePhoto, Upload, utcnow
from app.scripts.clean_uploads import clean
from app.scripts.import_refuge_photos import sync_refuge
from app.services import refuges_info
from tests.test_media import image_bytes


def item(external_id: int, day: int, author: str = "Alain") -> dict:
    return {
        "external_id": external_id,
        "url": f"https://www.refuges.info/photos_points/{external_id}-reduite.jpeg?md=x",
        "author": author,
        "caption": f"Photo {external_id}",
        "taken_at": datetime(2025, 1, day),
    }


@pytest.fixture
def refuge(db: Session) -> Refuge:
    refuge = Refuge(
        external_id=1550, name="Refuge du Glacier Blanc", kind=RefugeKind.GUARDED_HUT,
        latitude=44.934, longitude=6.4005,
    )  # fmt: skip
    db.add(refuge)
    db.commit()
    return refuge


@pytest.fixture
def downloads(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    fetched: list[str] = []

    def fake_fetch(url: str, max_bytes: int) -> bytes:
        fetched.append(url)
        return image_bytes()

    monkeypatch.setattr(refuges_info, "fetch_image", fake_fetch)
    return fetched


def test_fix_photo_path():
    fix = refuges_info._fix_photo_path
    assert fix("/photos_points/1-reduite.jpegmd=ab") == "/photos_points/1-reduite.jpeg?md=ab"
    assert fix("/photos_points/1-reduite.jpeg?md=ab") == "/photos_points/1-reduite.jpeg?md=ab"
    assert fix("/photos_points/1-reduite.jpeg") == "/photos_points/1-reduite.jpeg"


def test_photos_are_copied_and_served(active_client, db, refuge, downloads):
    added, _ = sync_refuge(db, refuge, [item(3, 3), item(2, 2), item(1, 1)], per_refuge=2)
    db.commit()

    assert added == 2 and len(downloads) == 2
    detail = active_client.get(f"/api/refuges/{refuge.id}").json()
    assert [p["caption"] for p in detail["photos"]] == ["Photo 3", "Photo 2"]
    assert detail["photos"][0]["author"] == "Alain"
    url = detail["photos"][0]["url"]
    assert url.startswith("/api/media/")
    response = active_client.get(url)
    assert response.status_code == 200 and response.headers["content-type"] == "image/webp"
    assert refuge.photos_checked_at is not None


def test_photos_need_an_account(client, db, refuge, downloads):
    sync_refuge(db, refuge, [item(1, 1)], per_refuge=3)
    db.commit()
    key = db.scalar(select(Upload.key))

    assert client.get(f"/api/media/{key}.webp").status_code == 401


def test_rerun_keeps_copies_and_follows_removals(db, refuge, downloads):
    sync_refuge(db, refuge, [item(2, 2), item(1, 1)], per_refuge=3)
    db.commit()

    added, removed = sync_refuge(db, refuge, [item(3, 3), item(2, 2)], per_refuge=3)
    db.commit()

    assert (added, removed) == (1, 1)
    assert len(downloads) == 3  # la photo 2 n'est pas retéléchargée
    ids = db.scalars(select(RefugePhoto.external_id).order_by(RefugePhoto.position)).all()
    assert ids == [3, 2]
    # L'image de la photo retirée est supprimée avec elle.
    orphans = select(Upload.id).where(Upload.id.not_in(select(RefugePhoto.upload_id)))
    assert db.scalar(orphans) is None


def test_failed_download_is_skipped(db, refuge, monkeypatch):
    def broken(url: str, max_bytes: int) -> bytes:
        raise OSError("404")

    monkeypatch.setattr(refuges_info, "fetch_image", broken)
    added, _ = sync_refuge(db, refuge, [item(1, 1)], per_refuge=3)
    db.commit()

    assert added == 0 and refuge.photos == []


def test_clean_keeps_refuge_photos(db, refuge, downloads):
    sync_refuge(db, refuge, [item(1, 1)], per_refuge=3)
    db.commit()

    rows, _ = clean(db, now=utcnow() + timedelta(days=2))

    assert rows == 0
    assert db.scalar(select(RefugePhoto.id)) is not None
