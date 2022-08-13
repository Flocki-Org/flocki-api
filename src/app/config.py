from pydantic import BaseSettings
from typing import Set

class Settings(BaseSettings):
    flocki_api_db_user_name: str = "postgres"
    flocki_api_db_password: str = "password"
    flocki_api_db_name: str = "flocki_api"
    flocki_api_db_port = 5432
    flocki_api_db_host = "localhost"

    flocki_app_port = 8000
    secret_key: str = "secret_key"
    token_expiry_minutes: int = 20
    image_store: str = "local" # local or s3 (aws)
    image_base_path: str = "./images"

    flocki_cors_origins: Set[str] = set()
    flocki_cors_origins.add("http://localhost:3000")

    class Config:
        env_file = ".env"

settings = Settings()