from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models import Profile, ProfileGallery
from app.schemas import ProfileOut, GalleryItem, ProfileUpdate
from app.models import User
from app.routes.media import save_base64_image

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/me", response_model=ProfileOut)
def me(user: User = Depends(get_current_user)):
    p = user.profile
    return ProfileOut(
        role=user.role,
        email=user.email,
        display_name=p.display_name,
        profile_image_url=p.profile_image_url,
        last_name_change_at=p.last_name_change_at.isoformat() if p.last_name_change_at else None,

        bio=p.bio,
        artistic_style=p.artistic_style,

        category=p.category,
        street=p.street,
        number=p.number,
        postal_code=p.postal_code,
        colony=p.colony,
        municipality=p.municipality,

        gallery=[GalleryItem(id=g.id, image_url=g.image_url) for g in user.gallery]
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

    if user.role == "artist":
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
    if not prof:
        raise HTTPException(404, "Profile not found")

    prof.profile_image_url = save_base64_image(data_url)

    db.commit()
    db.refresh(prof)

    return {"ok": True, "profile_image_url": prof.profile_image_url}

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
        urls.append(url)

    db.commit()
    return {"ok": True, "items": urls}


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
