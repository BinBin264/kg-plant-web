from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql+psycopg2://plantlib_user:plantlib123@db:5432/plant_lib"
    )

settings = Settings()
