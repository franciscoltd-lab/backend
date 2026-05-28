from sqlalchemy import Column, BigInteger, String, Text, DateTime, Enum, ForeignKey, TIMESTAMP, Numeric, func
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, index=True)
    role = Column(Enum("artist", "establishment", "admin"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete")
    gallery = relationship("ProfileGallery", back_populates="user", cascade="all, delete")
    events = relationship("Event", back_populates="establishment", cascade="all, delete")
    password_reset_codes = relationship("PasswordResetCode", back_populates="user", cascade="all, delete")


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    user = relationship("User", back_populates="password_reset_codes")

class Profile(Base):
    __tablename__ = "profiles"
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    display_name = Column(String(120), nullable=False)
    profile_image_url = Column(Text, nullable=True)
    last_name_change_at = Column(DateTime, nullable=True)

    bio = Column(Text, nullable=True)
    artistic_style = Column(String(120), nullable=True)

    category = Column(String(120), nullable=True)
    street = Column(String(180), nullable=True)
    number = Column(String(40), nullable=True)
    postal_code = Column(String(10), nullable=True)
    colony = Column(String(180), nullable=True)
    municipality = Column(String(180), nullable=True)

    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    user = relationship("User", back_populates="profile")

class ProfileGallery(Base):
    __tablename__ = "profile_gallery"
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(Text, nullable=False)
    title = Column(String(160), nullable=True)
    size = Column(String(80), nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    user = relationship("User", back_populates="gallery")


class Event(Base):
    __tablename__ = "events"
    id = Column(BigInteger, primary_key=True, index=True)
    establishment_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=True)
    location = Column(String(180), nullable=True)
    image_url = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    establishment = relationship("User", back_populates="events")
