from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .config import get_settings
from .routes import router

settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title=settings.app_name, version="1.0.0", description="AI-powered personalized fitness plan generator")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(router)
