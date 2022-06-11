from pydantic import BaseSettings

class Settings(BaseSettings):
    flocki_api_db_user_name: str = "postgres"
    flocki_api_db_password: str = "password"
    flocki_api_db_name: str = "flocki_api"
    flocki_api_db_port = 5432
    flocki_api_db_host = "localhost"

    class Config:
        env_file = ".env"

settings = Settings()