from pydantic import BaseSettings
from typing import Set

class Settings(BaseSettings):
    flocki_api_db_user_name: str = "postgres"
    flocki_api_db_password: str = "password"
    flocki_api_db_name: str = "flocki_api"
    flocki_api_db_port = 5432
    flocki_api_db_host = "localhost"

    flocki_app_port = 8000
    flocki_secret_key: str = "secret_key"
    flocki_token_expiry_minutes: int = 20
    flocki_media_store: str = "local" # local or s3 (aws)
    flocki_media_base_path: str = "./media"

    flocki_cors_origins: Set[str] = set()
    flocki_cors_origins.add("http://localhost:3000")


    flocki_s3_bucket_name = "flockiapp-s3"
    flocki_s3_region_name = "eu-west-1"
    flocki_s3_access_key = "" 
    flocki_s3_secret_access_key = ""

    flocki_google_client_id = "1026317288648-ig69iuhplrskjvuqtov66qu4bihlk27g.apps.googleusercontent.com"


    class Config:
        env_file = ".env"

settings = Settings()
