"""Images envoyées : traitement, rattachement aux posts et communautés, droit de lecture."""

import io
import os
import time
from datetime import timedelta

import pytest
from PIL import Image
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import (
    Community,
    CommunityMember,
    Friendship,
    FriendshipStatus,
    Role,
    Upload,
    User,
    utcnow,
)
from app.scripts.clean_uploads import clean


def image_bytes(size=(64, 48), format="JPEG", exif: Image.Exif | None = None) -> bytes:
    output = io.BytesIO()
    image = Image.new("RGB", size, (40, 120, 80))
    image.save(output, format, **({"exif": exif} if exif is not None else {}))
    return output.getvalue()


def upload(client, data: bytes | None = None, kind: str = "photo", name: str = "photo.jpg"):
    files = {"file": (name, data if data is not None else image_bytes(), "image/jpeg")}
    return client.post("/api/uploads", files=files, data={"kind": kind})


def user_id(db: Session, username: str) -> int:
    return db.scalar(select(User.id).where(User.username == username))


@pytest.fixture
def people(active_client, make_client, db: Session):
    """« randonneur » (moi), « camille » (amie), « lucas » (inconnu), « modo » (modérateur)."""
    clients = {
        "me": active_client,
        "friend": make_client("camille"),
        "stranger": make_client("lucas"),
        "modo": make_client("modo"),
    }
    db.add(
        Friendship(
            requester_id=user_id(db, "randonneur"),
            addressee_id=user_id(db, "camille"),
            status=FriendshipStatus.ACCEPTED,
        )
    )
    db.execute(update(User).where(User.username == "modo").values(role=Role.MODERATOR))
    db.commit()
    return clients


# ---------- Envoi et traitement ----------


def test_upload_is_reencoded_without_metadata(people, media_dir):
    exif = Image.Exif()
    exif[0x8825] = {2: (45.0, 0.0, 0.0)}  # GPSInfo : latitude de la prise de vue
    exif[0x0112] = 6  # Orientation : appareil tourné de 90°

    response = upload(people["me"], image_bytes((64, 48), exif=exif))

    assert response.status_code == 201
    body = response.json()
    # Image redressée selon l'orientation EXIF, puis réencodée en WebP sans métadonnées.
    assert (body["width"], body["height"]) == (48, 64)
    assert body["url"].startswith("/api/media/") and body["url"].endswith(".webp")
    stored = Image.open(next(media_dir.glob("*/*.webp")))
    assert stored.format == "WEBP"
    assert not stored.getexif()


def test_large_photo_is_resized_and_icon_is_square(people):
    photo = upload(people["me"], image_bytes((4000, 1000), format="PNG")).json()
    assert (photo["width"], photo["height"]) == (2048, 512)

    icon = upload(people["me"], image_bytes((800, 600)), kind="icon").json()
    assert (icon["width"], icon["height"]) == (512, 512)


@pytest.mark.parametrize(
    "data",
    [b"pas une image", image_bytes(format="GIF"), image_bytes()[:200]],
    ids=["texte", "gif", "tronquee"],
)
def test_invalid_images_are_rejected(people, data):
    response = upload(people["me"], data)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_image"


def test_too_large_file_is_rejected(people, monkeypatch):
    monkeypatch.setattr("app.routers.media.settings.upload_max_mb", 0)

    response = upload(people["me"])

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "file_too_large"


def test_upload_requires_an_account(client):
    assert upload(client).status_code == 401


def test_pending_uploads_are_limited(people, monkeypatch):
    monkeypatch.setattr("app.services.media.MAX_PENDING_UPLOADS", 2)
    upload(people["me"])
    upload(people["me"])

    response = upload(people["me"])

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "too_many_uploads"


# ---------- Photos des posts ----------


def publish(client, photo_ids, visibility="public", body="Glacier Blanc"):
    return client.post(
        "/api/posts", json={"body": body, "visibility": visibility, "photo_ids": photo_ids}
    )


def test_post_with_photos_in_order(people):
    first, second = (upload(people["me"]).json() for _ in range(2))

    response = publish(people["me"], [second["id"], first["id"]], body="")

    assert response.status_code == 201  # une photo seule suffit
    assert [photo["url"] for photo in response.json()["photos"]] == [second["url"], first["url"]]
    feed = people["friend"].get("/api/users/randonneur/posts").json()["items"]
    assert [photo["url"] for photo in feed[0]["photos"]] == [second["url"], first["url"]]


def test_post_photos_follow_post_visibility(people):
    photo = upload(people["me"]).json()
    publish(people["me"], [photo["id"]], visibility="friends")

    assert people["me"].get(photo["url"]).status_code == 200
    friend = people["friend"].get(photo["url"])
    assert friend.status_code == 200
    assert friend.headers["content-type"] == "image/webp"
    assert "private" in friend.headers["cache-control"]
    # Ni un inconnu, ni un modérateur hors signalement.
    assert people["stranger"].get(photo["url"]).status_code == 404
    assert people["modo"].get(photo["url"]).status_code == 404


def test_unpublished_upload_is_private(people):
    photo = upload(people["me"]).json()

    assert people["me"].get(photo["url"]).status_code == 200
    assert people["friend"].get(photo["url"]).status_code == 404


def test_cannot_use_someone_elses_or_an_already_used_photo(people):
    mine = upload(people["me"]).json()
    theirs = upload(people["stranger"]).json()

    stolen = publish(people["me"], [theirs["id"]])
    assert stolen.status_code == 422
    assert "photo_ids" in stolen.json()["detail"]["fields"]

    assert publish(people["me"], [mine["id"]]).status_code == 201
    assert publish(people["me"], [mine["id"]]).status_code == 422


def test_post_photo_limit(people):
    ids = [upload(people["me"]).json()["id"] for _ in range(5)]

    response = publish(people["me"], ids)

    assert response.status_code == 422
    assert response.json()["detail"]["fields"]["photo_ids"] == "4 photos au plus."


def test_empty_post_without_photo_is_rejected(people):
    response = publish(people["me"], [], body=" ")

    assert response.status_code == 422
    assert "photo" in response.json()["detail"]["fields"]["body"]


def test_moderator_sees_photos_of_reported_post(people):
    photo = upload(people["me"]).json()
    post_id = publish(people["me"], [photo["id"]], visibility="friends").json()["id"]
    people["friend"].post("/api/reports", json={"post_id": post_id, "reason": "spam"})

    assert people["modo"].get(photo["url"]).status_code == 200
    reports = people["modo"].get("/api/moderation/reports").json()
    assert reports[0]["post"]["photos"][0]["url"] == photo["url"]


def test_deleted_post_photos_are_no_longer_served(people):
    photo = upload(people["me"]).json()
    post_id = publish(people["me"], [photo["id"]]).json()["id"]

    people["me"].delete(f"/api/posts/{post_id}")

    assert people["friend"].get(photo["url"]).status_code == 404


# ---------- Visuels des communautés ----------


@pytest.fixture
def ecrins(db: Session) -> Community:
    community = Community(slug="ecrins", name="Écrins", region="Alpes")
    db.add(community)
    db.flush()
    db.add(CommunityMember(community_id=community.id, user_id=user_id(db, "randonneur")))
    db.commit()
    return community


def community_body(**visuals):
    return {"name": "Écrins", "description": "", "region": "Alpes", "refuge_ids": [], **visuals}


def test_community_banner_and_icon(people, ecrins):
    banner = upload(people["modo"], kind="banner").json()
    icon = upload(people["modo"], kind="icon").json()

    saved = people["modo"].put(
        "/api/moderation/communities/ecrins",
        json=community_body(banner_id=banner["id"], icon_id=icon["id"]),
    )

    assert saved.status_code == 200
    assert saved.json()["banner"]["id"] == banner["id"]
    detail = people["stranger"].get("/api/communities/ecrins").json()
    assert detail["banner"]["url"] == banner["url"] and detail["icon"]["url"] == icon["url"]
    listed = people["stranger"].get("/api/communities").json()
    assert listed[0]["banner"]["url"] == banner["url"]
    # Visible par tous, même sans être membre.
    assert people["stranger"].get(banner["url"]).status_code == 200

    # Enregistrer à nouveau garde les visuels ; null les retire.
    again = community_body(banner_id=banner["id"], icon_id=icon["id"])
    assert people["modo"].put("/api/moderation/communities/ecrins", json=again).status_code == 200
    removed = people["modo"].put("/api/moderation/communities/ecrins", json=community_body())
    assert removed.json()["banner"] is None and removed.json()["icon"] is None


def test_community_visual_must_be_a_fresh_upload_of_the_moderator(people, ecrins):
    others = upload(people["me"], kind="banner").json()
    photo = upload(people["modo"]).json()
    publish(people["modo"], [photo["id"]])

    for banner_id in (others["id"], photo["id"]):
        response = people["modo"].put(
            "/api/moderation/communities/ecrins", json=community_body(banner_id=banner_id)
        )
        assert response.status_code == 422
        assert "banner_id" in response.json()["detail"]["fields"]


# ---------- Nettoyage ----------


def test_clean_removes_old_unattached_uploads_and_orphan_files(people, db, media_dir):
    published = upload(people["me"]).json()
    publish(people["me"], [published["id"]])
    abandoned = upload(people["me"]).json()
    recent = upload(people["me"]).json()
    db.execute(
        update(Upload)
        .where(Upload.id.in_([published["id"], abandoned["id"]]))
        .values(created_at=utcnow() - timedelta(days=2))
    )
    db.commit()
    orphan = media_dir / "ab" / "abababababababababababababababab.webp"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_bytes(b"x")
    old = time.time() - timedelta(days=2).total_seconds()
    os.utime(orphan, (old, old))

    rows, files = clean(db)

    assert rows == 1 and files == 1
    remaining = set(db.scalars(select(Upload.id)))
    assert remaining == {published["id"], recent["id"]}
    assert not orphan.exists()
