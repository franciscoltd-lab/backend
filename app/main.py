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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:4200",
    "https://localhost",          # tu origen del error
    "capacitor://localhost",      # para app nativa
    "ionic://localhost",          # si lo usas
    # agrega aquí también el dominio del frontend si lo tienes en producción,
    # por ejemplo:
    # "https://mi-frontend.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # o ["*"] mientras pruebas (sin credenciales)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables (para MVP). Luego lo cambiamos a Alembic.
Base.metadata.create_all(bind=engine)

os.makedirs(settings.MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(public_router)
