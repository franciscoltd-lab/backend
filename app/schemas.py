from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal

Role = Literal["artist", "establishment", "admin"]

class RegisterArtist(BaseModel):
    role: Literal["artist"] = "artist"
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=3, max_length=120)
    artistic_style: str = Field(min_length=2, max_length=120)
    bio: str = Field(min_length=20)
    profile_image_base64: Optional[str] = None
    gallery_base64: List[str] = []

class RegisterEstablishment(BaseModel):
    role: Literal["establishment"] = "establishment"
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=120)
    street: str
    number: str
    postal_code: str
    colony: Optional[str] = None
    municipality: Optional[str] = None
    profile_image_base64: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetVerify(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8)

class MessageOut(BaseModel):
    message: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class GalleryItem(BaseModel):
    id: int
    image_url: str
    title: Optional[str] = None
    size: Optional[str] = None
    price: Optional[Decimal] = None
    description: Optional[str] = None


class ArtworkCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    size: Optional[str] = Field(default=None, max_length=80)
    price: Optional[Decimal] = Field(default=None, ge=0)
    description: Optional[str] = Field(default=None, max_length=3000)
    image_base64: str


class ArtworkUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=160)
    size: Optional[str] = Field(default=None, max_length=80)
    price: Optional[Decimal] = Field(default=None, ge=0)
    description: Optional[str] = Field(default=None, max_length=3000)
    image_base64: Optional[str] = None


class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: Optional[str] = Field(default=None, max_length=3000)
    starts_at: datetime
    ends_at: Optional[datetime] = None
    location: Optional[str] = Field(default=None, max_length=180)
    image_base64: Optional[str] = None
    image_url: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=160)
    description: Optional[str] = Field(default=None, max_length=3000)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    location: Optional[str] = Field(default=None, max_length=180)
    image_base64: Optional[str] = None
    image_url: Optional[str] = None


class EventOut(BaseModel):
    id: int
    establishment_id: int
    establishment_name: Optional[str] = None
    establishment_image_url: Optional[str] = None
    title: str
    description: Optional[str]
    starts_at: datetime
    ends_at: Optional[datetime]
    location: Optional[str]
    image_url: Optional[str]

class ProfileOut(BaseModel):
    role: Role
    email: EmailStr
    display_name: str
    profile_image_url: Optional[str]
    last_name_change_at: Optional[str]

    bio: Optional[str]
    artistic_style: Optional[str]

    category: Optional[str]
    street: Optional[str]
    number: Optional[str]
    postal_code: Optional[str]
    colony: Optional[str]
    municipality: Optional[str]

    gallery: List[GalleryItem] = []

class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=3, max_length=120)
    bio: Optional[str] = Field(default=None, min_length=20)
    artistic_style: Optional[str] = Field(default=None, min_length=2, max_length=120)
    category: Optional[str] = Field(default=None, min_length=2, max_length=120)

# app/schemas.py
class UpdateProfile(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    bio: Optional[str] = Field(default=None, min_length=0, max_length=2000)
    artistic_style: Optional[str] = Field(default=None, min_length=2, max_length=120)
    category: Optional[str] = Field(default=None, min_length=2, max_length=120)

    street: Optional[str] = None
    number: Optional[str] = None
    postal_code: Optional[str] = None
    colony: Optional[str] = None
    municipality: Optional[str] = None
