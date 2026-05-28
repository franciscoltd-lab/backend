from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models import Profile, ProfileGallery
from app.schemas import ArtworkCreate, ArtworkUpdate, GalleryItem, ProfileOut, ProfileUpdate
from app.models import User
from app.routes.media import save_base64_image, public_media_url

router = APIRouter(prefix="/profile", tags=["profile"])

DEFAULT_ADMIN_PROFILE_IMAGE = "assets/avatar-placeholder.png"

@router.get("/me", response_model=ProfileOut)
def me(user: User = Depends(get_current_user)):
    p = user.profile
    if user.role == "admin":
        if p:
            return ProfileOut(
                role=user.role,
                email=user.email,
                display_name=p.display_name,
                profile_image_url=public_media_url(p.profile_image_url),
                last_name_change_at=p.last_name_change_at.isoformat() if p.last_name_change_at else None,
                bio=p.bio,
                artistic_style=p.artistic_style,
                category=p.category,
                street=p.street,
                number=p.number,
                postal_code=p.postal_code,
                colony=p.colony,
                municipality=p.municipality,
                gallery=[serialize_artwork(g) for g in user.gallery],
            )

        return ProfileOut(
            role=user.role,
            email=user.email,
            display_name="Admin",
            profile_image_url=DEFAULT_ADMIN_PROFILE_IMAGE,
            last_name_change_at=None,
            bio=None,
            artistic_style=None,
            category=None,
            street=None,
            number=None,
            postal_code=None,
            colony=None,
            municipality=None,
            gallery=[serialize_artwork(g) for g in user.gallery],
        )

    if not p:
        raise HTTPException(404, "Profile not found")

    return ProfileOut(
        role=user.role,
        email=user.email,
        display_name=p.display_name,
        profile_image_url=public_media_url(p.profile_image_url),
        last_name_change_at=p.last_name_change_at.isoformat() if p.last_name_change_at else None,

        bio=p.bio,
        artistic_style=p.artistic_style,

        category=p.category,
        street=p.street,
        number=p.number,
        postal_code=p.postal_code,
        colony=p.colony,
        municipality=p.municipality,

        gallery=[serialize_artwork(g) for g in user.gallery]
    )


def require_artist(user: User):
    if user.role not in ("artist", "admin"):
        raise HTTPException(403, "Only artists can manage artworks")


def serialize_artwork(row: ProfileGallery) -> GalleryItem:
    return GalleryItem(
        id=row.id,
        image_url=public_media_url(row.image_url),
        title=row.title,
        size=row.size,
        price=row.price,
        description=row.description,
    )

@router.patch("/me", response_model=ProfileOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = user.profile

    # Regla nombre cada 30 días
    if payload.display_name and payload.display_name != p.display_name:
        if p.last_name_change_at and (datetime.utcnow() - p.last_name_change_at) < timedelta(days=30):
            raise HTTPException(409, "Display name can only be changed every 30 days")
        p.display_name = payload.display_name
        p.last_name_change_at = datetime.utcnow()

    if user.role in ("artist", "admin"):
        if payload.bio is not None:
            p.bio = payload.bio
        if payload.artistic_style is not None:
            p.artistic_style = payload.artistic_style

    if user.role == "establishment":
        if payload.category is not None:
            p.category = payload.category

    db.commit()
    db.refresh(user)

    return me(user)

import logging
logger = logging.getLogger(__name__)


@router.post("/me/profile-image")
def set_profile_image(
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    
    logger.info(">>> set_profile_image CALLED user=%s", user.id)

    data_url = body.get("profile_image_base64")
    if not data_url:
        raise HTTPException(422, "profile_image_base64 required")

    prof = db.query(Profile).filter(Profile.user_id == user.id).first()
    if not prof and user.role == "admin":
        prof = Profile(
            user_id=user.id,
            display_name="Admin",
            bio="Perfil de prueba para administrar y validar la experiencia de artista.",
            artistic_style="Pruebas internas",
        )
        db.add(prof)
        db.flush()

    if not prof:
        raise HTTPException(404, "Profile not found")

    prof.profile_image_url = save_base64_image(data_url)

    db.commit()
    db.refresh(prof)

    return {"ok": True, "profile_image_url": public_media_url(prof.profile_image_url)}

@router.post("/me/gallery")
def add_gallery(
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    images = body.get("gallery_base64") or []
    if not isinstance(images, list) or not images:
        raise HTTPException(422, "gallery_base64 must be a non-empty list")

    urls = []
    for img in images:
        url = save_base64_image(img)
        db.add(ProfileGallery(user_id=user.id, image_url=url))
        urls.append(public_media_url(url))

    db.commit()
    return {"ok": True, "items": urls}


@router.get("/me/artworks", response_model=list[GalleryItem])
def list_artworks(
    user: User = Depends(get_current_user),
):
    require_artist(user)
    return [serialize_artwork(row) for row in user.gallery]


@router.post("/me/artworks", response_model=GalleryItem)
def create_artwork(
    payload: ArtworkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_artist(user)

    row = ProfileGallery(
        user_id=user.id,
        image_url=save_base64_image(payload.image_base64),
        title=payload.title,
        size=payload.size,
        price=payload.price,
        description=payload.description,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_artwork(row)


@router.patch("/me/artworks/{artwork_id}", response_model=GalleryItem)
def update_artwork(
    artwork_id: int,
    payload: ArtworkUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_artist(user)

    row = db.query(ProfileGallery).filter(
        ProfileGallery.id == artwork_id,
        ProfileGallery.user_id == user.id,
    ).first()
    if not row:
        raise HTTPException(404, "Artwork not found")

    data = payload.model_dump(exclude_unset=True)
    image_base64 = data.pop("image_base64", None)
    if image_base64:
        row.image_url = save_base64_image(image_base64)

    for key, value in data.items():
        setattr(row, key, value)

    db.commit()
    db.refresh(row)
    return serialize_artwork(row)


@router.delete("/me/artworks/{artwork_id}")
def delete_artwork(
    artwork_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_artist(user)

    row = db.query(ProfileGallery).filter(
        ProfileGallery.id == artwork_id,
        ProfileGallery.user_id == user.id,
    ).first()

    if not row:
        raise HTTPException(404, "Artwork not found")

    db.delete(row)
    db.commit()
    return {"ok": True}


@router.delete("/me/gallery/{gallery_id}")
def delete_gallery_item(
    gallery_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.query(ProfileGallery).filter(
        ProfileGallery.id == gallery_id,
        ProfileGallery.user_id == user.id
    ).first()

    if not row:
        raise HTTPException(404, "Not found")

    db.delete(row)
    db.commit()
    return {"ok": True}
