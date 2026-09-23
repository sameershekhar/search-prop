import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """Runtime configuration, overridable via environment variables."""
    data_file_path: Path = Path(
        os.getenv("SEARCHPROP_DATA_FILE", str(BASE_DIR / "data" / "listings.json"))
    )
    cors_origins: list[str] = os.getenv(
        "SEARCHPROP_CORS_ORIGINS", "http://localhost:5173,https://se-e78cb691e6cf4a2c95cdb4e6124b1e39.ecs.ap-south-1.on.aws"
    ).split(",")


settings = Settings()
