from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    fe_url: str


settings = Settings()
