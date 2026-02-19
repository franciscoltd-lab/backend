from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db
from app.models import User, Profile, ProfileGallery
from app.schemas import RegisterArtist, RegisterEstablishment, LoginIn, TokenOut
from app.core.security import hash_password, verify_password, create_access_token
from app.routes.media import save_base64_image

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register-artist", response_model=TokenOut)
def register_artist(payload: RegisterArtist, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(409, "Email already registered")
    user = User(role="artist", email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()  # to get user.id

    profile_image_url = save_base64_image(payload.profile_image_base64) if payload.profile_image_base64 else None

    profile = Profile(
        user_id=user.id,
        display_name=payload.display_name,
        profile_image_url=profile_image_url,
        bio=payload.bio,
        artistic_style=payload.artistic_style
    )
    db.add(profile)

    for img in payload.gallery_base64:
        url = save_base64_image(img)
        db.add(ProfileGallery(user_id=user.id, image_url=url))

    db.commit()

    token = create_access_token(sub=str(user.id), role=user.role)
    return TokenOut(access_token=token)

@router.post("/register-establishment", response_model=TokenOut)
def register_est(payload: RegisterEstablishment, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(409, "Email already registered")

    user = User(role="establishment", email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()

    profile_image_url = save_base64_image(payload.profile_image_base64) if payload.profile_image_base64 else None

    profile = Profile(
        user_id=user.id,
        display_name=payload.display_name,
        profile_image_url=profile_image_url,
        category=payload.category,
        street=payload.street,
        number=payload.number,
        postal_code=payload.postal_code,
        colony=payload.colony,
        municipality=payload.municipality,
    )
    db.add(profile)
    db.commit()

    token = create_access_token(sub=str(user.id), role=user.role)
    return TokenOut(access_token=token)

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token(sub=str(user.id), role=user.role)
    return TokenOut(access_token=token)
