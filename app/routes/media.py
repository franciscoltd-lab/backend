import os, base64, uuid
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/media", tags=["media"])

def save_base64_image(data_url: str) -> str:
    # data:image/png;base64,....
    header, b64 = data_url.split(",", 1)
    ext = "jpg"
    if "image/" in header:
      ext = header.split("image/")[1].split(";")[0]

    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(settings.MEDIA_DIR, name)

    with open(path, "wb") as f:
      f.write(base64.b64decode(b64))

    return f"{settings.PUBLIC_MEDIA_BASE}/{name}"


def public_media_url(url: str | None) -> str | None:
    if not url:
        return None

    marker = "/media/"
    if marker in url:
        name = url.rsplit(marker, 1)[1].lstrip("/")
        return f"{settings.PUBLIC_MEDIA_BASE}/{name}"

    if url.startswith("media/"):
        return f"{settings.PUBLIC_MEDIA_BASE}/{url.split('/', 1)[1]}"

    return url
