from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db
from app.models import User, Profile, ProfileGallery, PasswordResetCode
from app.schemas import (
    RegisterArtist,
    RegisterEstablishment,
    LoginIn,
    TokenOut,
    PasswordResetRequest,
    PasswordResetVerify,
    PasswordResetConfirm,
    MessageOut,
)
from app.core.security import hash_password, verify_password, create_access_token
from app.core.email import send_password_reset_code
from app.routes.media import save_base64_image

import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _utcnow() -> datetime:
    return datetime.utcnow()


def _find_valid_reset_code(db: Session, user_id: int, code: str) -> PasswordResetCode | None:
    candidates = (
        db.query(PasswordResetCode)
        .filter(
            PasswordResetCode.user_id == user_id,
            PasswordResetCode.used_at.is_(None),
            PasswordResetCode.expires_at > _utcnow(),
        )
        .order_by(PasswordResetCode.created_at.desc())
        .all()
    )
    for item in candidates:
        if verify_password(code, item.code_hash):
            return item
    return None

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


@router.post("/password-reset/request", response_model=MessageOut)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    generic_message = "Si el correo existe, enviaremos un codigo de recuperacion."

    if not user:
        return MessageOut(message=generic_message)

    code = f"{secrets.randbelow(1_000_000):06d}"
    reset_code = PasswordResetCode(
        user_id=user.id,
        code_hash=hash_password(code),
        expires_at=_utcnow() + timedelta(minutes=10),
    )
    db.add(reset_code)
    db.commit()
   

    try:
        send_password_reset_code(user.email, code)
    except Exception as e:
        logger.exception("Password reset email failed")
        db.delete(reset_code)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Error enviando correo: {str(e)}"
        )

    return MessageOut(message=generic_message)


@router.post("/password-reset/verify", response_model=MessageOut)
def verify_password_reset_code(payload: PasswordResetVerify, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not _find_valid_reset_code(db, user.id, payload.code):
        raise HTTPException(400, "Codigo invalido o expirado")

    return MessageOut(message="Codigo valido.")


@router.post("/password-reset/confirm", response_model=MessageOut)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(400, "Codigo invalido o expirado")

    reset_code = _find_valid_reset_code(db, user.id, payload.code)
    if not reset_code:
        raise HTTPException(400, "Codigo invalido o expirado")

    user.password_hash = hash_password(payload.new_password)
    reset_code.used_at = _utcnow()
    db.commit()

    return MessageOut(message="Contrasena actualizada.")
