import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.deps import get_db
from app.models import Event, User, Profile, ProfileGallery
from app.core.config import settings
from app.routes.media import public_media_url


router = APIRouter(prefix="/public", tags=["public"])

ACCENT_REPLACEMENTS = (
    ("á", "a"), ("à", "a"), ("ä", "a"), ("â", "a"),
    ("é", "e"), ("è", "e"), ("ë", "e"), ("ê", "e"),
    ("í", "i"), ("ì", "i"), ("ï", "i"), ("î", "i"),
    ("ó", "o"), ("ò", "o"), ("ö", "o"), ("ô", "o"),
    ("ú", "u"), ("ù", "u"), ("ü", "u"), ("û", "u"),
    ("ñ", "n"),
)


def normalize_search_text(value: str) -> str:
    value = value.strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    for accented, plain in ACCENT_REPLACEMENTS:
        value = value.replace(accented, plain)
    return value


def matches_normalized(value: str | None, search: str) -> bool:
    if not value:
        return False
    return normalize_search_text(search) in normalize_search_text(value)


def normalized_column(column):
    expr = func.lower(column)
    for accented, plain in ACCENT_REPLACEMENTS:
        expr = func.replace(expr, accented, plain)
        expr = func.replace(expr, accented.upper(), plain)
    return expr


def normalized_like(column, search: str):
    return normalized_column(column).like(f"%{normalize_search_text(search)}%")


def paginate(page: int, size: int):
    page = max(page, 1)
    size = min(max(size, 1), 50)
    return (page - 1) * size, size

@router.get("/artists")
def list_artists(
    search: str | None = Query(default=None),
    search_field: str | None = Query(default=None),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    offset, limit = paginate(page, size)

    q = (
        db.query(User.id, Profile.display_name, Profile.profile_image_url, Profile.artistic_style)
        .join(Profile, Profile.user_id == User.id)
        .filter(User.role == "artist")
    )

    rows = q.all()

    if search:
        if search_field == "name":
            rows = [r for r in rows if matches_normalized(r.display_name, search)]
        elif search_field == "style":
            rows = [r for r in rows if matches_normalized(r.artistic_style, search)]
        else:
            rows = [
                r for r in rows
                if matches_normalized(r.display_name, search) or matches_normalized(r.artistic_style, search)
            ]

    total = len(rows)
    rows = rows[offset:offset + limit]

    return {
        "page": page,
        "size": limit,
        "total": total,
        "items": [
            {
                "user_id": r.id,
                "display_name": r.display_name,
                "profile_image_url": public_media_url(r.profile_image_url),
                "artistic_style": r.artistic_style,
            }
            for r in rows
        ],
    }

@router.get("/establishments")
def list_establishments(
    search: str | None = Query(default=None),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    offset, limit = paginate(page, size)

    q = (
        db.query(User.id, Profile.display_name, Profile.profile_image_url, Profile.category, Profile.municipality)
        .join(Profile, Profile.user_id == User.id)
        .filter(User.role == "establishment")
    )

    if search:
        s = f"%{search.strip()}%"
        q = q.filter(or_(
            Profile.display_name.like(s),
            Profile.category.like(s),
            Profile.municipality.like(s),
        ))

    total = q.count()
    rows = q.offset(offset).limit(limit).all()

    return {
        "page": page,
        "size": limit,
        "total": total,
        "items": [
            {
                "user_id": r.id,
                "display_name": r.display_name,
                "profile_image_url": public_media_url(r.profile_image_url),
                "category": r.category,
                "municipality": r.municipality,
            }
            for r in rows
        ],
    }

@router.get("/artworks")
def list_artworks(
    search: str | None = Query(default=None),
    search_field: str | None = Query(default=None),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    offset, limit = paginate(page, size)

    # obras = ProfileGallery (asumiendo que ahí guardas imágenes)
    q = (
        db.query(
            ProfileGallery.id,
            ProfileGallery.image_url,
            ProfileGallery.title,
            ProfileGallery.size,
            ProfileGallery.price,
            ProfileGallery.description,
            User.id.label("user_id"),
            Profile.display_name,
        )
        .join(User, User.id == ProfileGallery.user_id)
        .join(Profile, Profile.user_id == User.id)
    )

    if search:
        s = f"%{search.strip()}%"
        if search_field == "name":
            q = q.filter(normalized_like(Profile.display_name, search))
        elif search_field == "style":
            q = q.filter(Profile.artistic_style.like(s))
        else:
            q = q.filter(or_(
                normalized_like(Profile.display_name, search),
                Profile.artistic_style.like(s),
            ))

    total = q.count()
    rows = q.offset(offset).limit(limit).all()

    return {
        "page": page,
        "size": limit,
        "total": total,
        "items": [
            {
                "gallery_id": r.id,
                "image_url": public_media_url(r.image_url),
                "title": r.title,
                "size": r.size,
                "price": float(r.price) if r.price is not None else None,
                "description": r.description,
                "user_id": r.user_id,
                "display_name": r.display_name,
            }
            for r in rows
        ],
    }


@router.get("/events")
def list_events(
    search: str | None = Query(default=None),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    offset, limit = paginate(page, size)

    q = (
        db.query(
            Event.id,
            Event.establishment_id,
            Event.title,
            Event.description,
            Event.starts_at,
            Event.ends_at,
            Event.location,
            Event.image_url,
            Profile.display_name.label("establishment_name"),
            Profile.profile_image_url.label("establishment_image_url"),
        )
        .join(User, User.id == Event.establishment_id)
        .join(Profile, Profile.user_id == User.id)
        .filter(User.role == "establishment")
    )

    if search:
        s = f"%{search.strip()}%"
        q = q.filter(or_(
            Event.title.like(s),
            Event.description.like(s),
            Event.location.like(s),
            Profile.display_name.like(s),
            Profile.category.like(s),
        ))

    total = q.count()
    rows = q.order_by(Event.starts_at.asc()).offset(offset).limit(limit).all()

    return {
        "page": page,
        "size": limit,
        "total": total,
        "items": [
            {
                "id": r.id,
                "establishment_id": r.establishment_id,
                "establishment_name": r.establishment_name,
                "establishment_image_url": public_media_url(r.establishment_image_url),
                "title": r.title,
                "description": r.description,
                "starts_at": r.starts_at.isoformat() if r.starts_at else None,
                "ends_at": r.ends_at.isoformat() if r.ends_at else None,
                "location": r.location,
                "image_url": public_media_url(r.image_url),
            }
            for r in rows
        ],
    }

@router.get("/home")
def home_swipers(
    artists_size: int = Query(10, ge=1, le=30),
    establishments_size: int = Query(10, ge=1, le=30),
    artworks_size: int = Query(10, ge=1, le=30),
    events_size: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    # --- ARTISTS (cards para swiper) ---
    artists_rows = (
        db.query(User.id, Profile.display_name, Profile.profile_image_url, Profile.artistic_style)
        .join(Profile, Profile.user_id == User.id)
        .filter(User.role == "artist")
        .order_by(func.rand())  # MySQL
        .limit(artists_size)
        .all()
    )

    # --- ESTABLISHMENTS (cards para swiper) ---
    est_rows = (
        db.query(User.id, Profile.display_name, Profile.profile_image_url, Profile.category, Profile.municipality)
        .join(Profile, Profile.user_id == User.id)
        .filter(User.role == "establishment")
        .order_by(func.rand())
        .limit(establishments_size)
        .all()
    )

    # --- ARTWORKS (slides de obras, usando ProfileGallery) ---
    artworks_rows = (
        db.query(
            ProfileGallery.id,
            ProfileGallery.image_url,
            ProfileGallery.title,
            ProfileGallery.size,
            ProfileGallery.price,
            ProfileGallery.description,
            User.id.label("user_id"),
            Profile.display_name.label("artist_name"),
        )
        .join(User, User.id == ProfileGallery.user_id)
        .join(Profile, Profile.user_id == User.id)
        .filter(User.role == "artist")
        .order_by(func.rand())
        .limit(artworks_size)
        .all()
    )

    # --- EVENTS (featured slides tied to establishments) ---
    events_rows = (
        db.query(
            Event.id,
            Event.establishment_id,
            Event.title,
            Event.description,
            Event.starts_at,
            Event.ends_at,
            Event.location,
            Event.image_url,
            Profile.display_name.label("establishment_name"),
            Profile.profile_image_url.label("establishment_image_url"),
        )
        .join(User, User.id == Event.establishment_id)
        .join(Profile, Profile.user_id == User.id)
        .filter(User.role == "establishment")
        .order_by(func.rand())
        .limit(events_size)
        .all()
    )

    return {
        "events": [
            {
                "id": r.id,
                "establishment_id": r.establishment_id,
                "establishment_name": r.establishment_name,
                "establishment_image_url": public_media_url(r.establishment_image_url),
                "title": r.title,
                "description": r.description,
                "starts_at": r.starts_at.isoformat() if r.starts_at else None,
                "ends_at": r.ends_at.isoformat() if r.ends_at else None,
                "location": r.location,
                "image_url": public_media_url(r.image_url),
            }
            for r in events_rows
        ],
        "artists": [
            {
                "user_id": r.id,
                "display_name": r.display_name,
                "profile_image_url": public_media_url(r.profile_image_url),
                "artistic_style": r.artistic_style,
            }
            for r in artists_rows
        ],
        "establishments": [
            {
                "user_id": r.id,
                "display_name": r.display_name,
                "profile_image_url": public_media_url(r.profile_image_url),
                "category": r.category,
                "municipality": r.municipality,
            }
            for r in est_rows
        ],
        "artworks": [
            {
                "gallery_id": r.id,
                "image_url": public_media_url(r.image_url),
                "title": r.title,
                "size": r.size,
                "price": float(r.price) if r.price is not None else None,
                "description": r.description,
                "user_id": r.user_id,
                "artist_name": r.artist_name,
            }
            for r in artworks_rows
        ],
    }

@router.get("/artist/{user_id}")
def get_public_artist(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.id == user_id,
        User.role == "artist"
    ).first()

    if not user:
        raise HTTPException(404, "Artist not found")

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    gallery = db.query(ProfileGallery).filter(
        ProfileGallery.user_id == user_id
    ).all()

    return {
        "user_id": user.id,
        "display_name": profile.display_name,
        "profile_image_url": public_media_url(profile.profile_image_url),
        "bio": profile.bio,
        "artistic_style": profile.artistic_style,
        "gallery": [
            {
                "id": g.id,
                "image_url": public_media_url(g.image_url),
                "title": g.title,
                "size": g.size,
                "price": float(g.price) if g.price is not None else None,
                "description": g.description,
            }
            for g in gallery
        ]
    }


@router.get("/establishment/{user_id}")
def get_public_establishment(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.id == user_id,
        User.role == "establishment"
    ).first()

    if not user:
        raise HTTPException(404, "Establishment not found")

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    # OJO: normalmente establishments NO tienen gallery, pero si luego quieres fotos del lugar:
    # gallery = db.query(ProfileGallery).filter(ProfileGallery.user_id == user_id).all()

    return {
        "user_id": user.id,
        "display_name": profile.display_name,
        "profile_image_url": public_media_url(profile.profile_image_url),
        "category": profile.category,
        "street": profile.street,
        "number": profile.number,
        "postal_code": profile.postal_code,
        "colony": profile.colony,
        "municipality": profile.municipality,
        # "gallery": [{"id": g.id, "image_url": g.image_url} for g in gallery],
    }


class BankInfoOut(BaseModel):
    bank: str
    account: str
    clabe: str

@router.get("/bank-info", response_model=BankInfoOut)
def get_bank_info():
    return BankInfoOut(
        bank=settings.BANK_NAME,
        account=settings.BANK_ACCOUNT,
        clabe=settings.BANK_CLABE,
    )
