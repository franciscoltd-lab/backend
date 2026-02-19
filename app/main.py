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

origins = [
    "http://localhost",
    "http://localhost:4200",
    "capacitor://localhost",
    "ionic://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
