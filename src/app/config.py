from typing import Set

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    flocki_api_db_user_name: str = "postgres"
    flocki_api_db_password: str = "password"
    flocki_api_db_name: str = "flocki_api"
    flocki_api_db_port: int = 5432
    flocki_api_db_host: str = "localhost"

    flocki_app_port: int = 8000
    flocki_secret_key: str = "gmWtYRS6i4D9Uh8okfsYy4u_qacpz09vlIOQzWTpQgk"
    flocki_token_expiry_minutes: int = 20
    flocki_media_store: str = "local" # local or s3 (aws)
    flocki_media_base_path: str = "./media"

    flocki_cors_origins: Set[str] = {"http://localhost:3000"}

    flocki_s3_bucket_name: str = "flockiapp-s3"
    flocki_s3_region_name: str = "eu-west-1"
    flocki_s3_access_key: str = ""
    flocki_s3_secret_access_key: str = ""

    flocki_google_client_id: str = "1026317288648-ig69iuhplrskjvuqtov66qu4bihlk27g.apps.googleusercontent.com"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
