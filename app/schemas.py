from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal

Role = Literal["artist", "establishment"]

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

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class GalleryItem(BaseModel):
    id: int
    image_url: str

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
