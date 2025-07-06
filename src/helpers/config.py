from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str
    OPENAI_API_KEY: str

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int
    MONGODB_URL:str
    MONGODB_DATABASE:str

    class Config:
        env_file = ".env"

@lru_cache(maxsize=1) # make it cache only one in order to make a singleton class 
def get_settings():
    return Settings()