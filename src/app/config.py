from typing import Optional, Set

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Prefer a single URL when present (Render injects DATABASE_URL when a DB is linked).
    flocki_api_database_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "FLOCKI_API_DATABASE_URL",
            "DATABASE_URL",
            "flocki_api_database_url",
        ),
    )

    flocki_api_db_user_name: str = "postgres"
    flocki_api_db_password: str = "password"
    flocki_api_db_name: str = "flocki_api"
    flocki_api_db_port: int = 5432
    flocki_api_db_host: str = "localhost"

    # When FLOCKI_API_DB_HOST is a bare Render internal id (dpg-…-a) that does not
    # resolve (region mismatch / no private DNS), expand to the external hostname
    # using this region, e.g. oregon → dpg-…-a.oregon-postgres.render.com.
    flocki_api_db_render_region: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "FLOCKI_API_DB_RENDER_REGION",
            "RENDER_REGION",
            "flocki_api_db_render_region",
        ),
    )

    # Force TLS. Render external (and recommended internal) Postgres requires it.
    # Examples: require, prefer, disable. None = auto (require for *.render.com).
    flocki_api_db_sslmode: Optional[str] = None

    flocki_app_port: int = 8000
    flocki_secret_key: str = "gmWtYRS6i4D9Uh8okfsYy4u_qacpz09vlIOQzWTpQgk"
    flocki_token_expiry_minutes: int = 20
    flocki_media_store: str = "local"  # local or s3 (aws)
    flocki_media_base_path: str = "./media"

    flocki_cors_origins: Set[str] = {"http://localhost:3000"}

    flocki_s3_bucket_name: str = "flockiapp-s3"
    flocki_s3_region_name: str = "eu-west-1"
    flocki_s3_access_key: str = ""
    flocki_s3_secret_access_key: str = ""

    flocki_google_client_id: str = "1026317288648-ig69iuhplrskjvuqtov66qu4bihlk27g.apps.googleusercontent.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
