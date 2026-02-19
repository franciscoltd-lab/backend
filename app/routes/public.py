from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.deps import get_db
from app.models import User, Profile, ProfileGallery

router = APIRouter(prefix="/public", tags=["public"])

def paginate(page: int, size: int):
    page = max(page, 1)
    size = min(max(size, 1), 50)
    return (page - 1) * size, size

@router.get("/artists")
def list_artists(
    search: str | None = Query(default=None),
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

    if search:
        s = f"%{search.strip()}%"
        q = q.filter(or_(
            Profile.display_name.like(s),
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
                "user_id": r.id,
                "display_name": r.display_name,
                "profile_image_url": r.profile_image_url,
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
                "profile_image_url": r.profile_image_url,
                "category": r.category,
                "municipality": r.municipality,
            }
            for r in rows
        ],
    }

@router.get("/artworks")
def list_artworks(
    search: str | None = Query(default=None),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    offset, limit = paginate(page, size)

    # obras = ProfileGallery (asumiendo que ahí guardas imágenes)
    q = (
        db.query(ProfileGallery.id, ProfileGallery.image_url, User.id.label("user_id"), Profile.display_name)
        .join(User, User.id == ProfileGallery.user_id)
        .join(Profile, Profile.user_id == User.id)
    )

    if search:
        s = f"%{search.strip()}%"
        q = q.filter(Profile.display_name.like(s))

    total = q.count()
    rows = q.offset(offset).limit(limit).all()

    return {
        "page": page,
        "size": limit,
        "total": total,
        "items": [
            {
                "gallery_id": r.id,
                "image_url": r.image_url,
                "user_id": r.user_id,
                "display_name": r.display_name,
            }
            for r in rows
        ],
    }

@router.get("/home")
def home_swipers(
    artists_size: int = Query(10, ge=1, le=30),
    establishments_size: int = Query(10, ge=1, le=30),
    artworks_size: int = Query(10, ge=1, le=30),
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

    return {
        "artists": [
            {
                "user_id": r.id,
                "display_name": r.display_name,
                "profile_image_url": r.profile_image_url,
                "artistic_style": r.artistic_style,
            }
            for r in artists_rows
        ],
        "establishments": [
            {
                "user_id": r.id,
                "display_name": r.display_name,
                "profile_image_url": r.profile_image_url,
                "category": r.category,
                "municipality": r.municipality,
            }
            for r in est_rows
        ],
        "artworks": [
            {
                "gallery_id": r.id,
                "image_url": r.image_url,
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
        "profile_image_url": profile.profile_image_url,
        "bio": profile.bio,
        "artistic_style": profile.artistic_style,
        "gallery": [
            {"id": g.id, "image_url": g.image_url}
            for g in gallery
        ]
    }
