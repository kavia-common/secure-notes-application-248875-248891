import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

# Load .env if present (the platform provides it; this is safe in all envs).
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    app_name: str
    environment: str

    # CORS
    cors_allow_origins: List[str]

    # DB
    postgres_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_exp_minutes: int


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            f"Please add it to the notes_backend .env via orchestration."
        )
    return value


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an int") from exc


def _parse_csv_env(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """PUBLIC_INTERFACE: Load and validate Settings from environment variables."""
    env = os.getenv("ENVIRONMENT", "development")

    # Match database container env var names provided by orchestrator.
    # Required by work item: POSTGRES_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT
    postgres_url = _get_required_env("POSTGRES_URL")
    postgres_user = _get_required_env("POSTGRES_USER")
    postgres_password = _get_required_env("POSTGRES_PASSWORD")
    postgres_db = _get_required_env("POSTGRES_DB")
    postgres_port = _get_required_env("POSTGRES_PORT")

    # JWT secret must be provided per environment.
    jwt_secret_key = _get_required_env("JWT_SECRET_KEY")

    cors_default = "http://localhost:3000"
    cors_origins = _parse_csv_env("CORS_ALLOW_ORIGINS", cors_default)

    return Settings(
        app_name=os.getenv("APP_NAME", "Secure Notes API"),
        environment=env,
        cors_allow_origins=cors_origins,
        postgres_url=postgres_url,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_db=postgres_db,
        postgres_port=postgres_port,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_access_token_exp_minutes=_get_int_env("JWT_ACCESS_TOKEN_EXP_MINUTES", 60 * 24),
    )
