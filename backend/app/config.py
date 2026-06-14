import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    DATA_DIR = BASE_DIR / "data"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{DATA_DIR / 'milk_tea_purchase.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False
