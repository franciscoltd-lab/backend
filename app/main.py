import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db.session import engine
from app.models import Base
from app.core.config import settings

from app.routes.auth import router as auth_router
from app.routes.profile import router as profile_router
from app.routes.public import router as public_router

app = FastAPI(title="Quetzart API")

# 👇 Orígenes permitidos
origins = [
    "http://localhost",
    "http://localhost:4200",
    "http://localhost:8100",      # ionic serve / capacitor web
    "https://localhost",
    "https://localhost:4200",
    "https://localhost:8100",
    "capacitor://localhost",      # app nativa
    "ionic://localhost",          # si lo usas
    # dominio(s) reales de tu frontend
    # "https://tusitio.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # lista concreta, NO varios en un header
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables (para MVP)
Base.metadata.create_all(bind=engine)

# Media
os.makedirs(settings.MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

# Rutas
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(public_router)