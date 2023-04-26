from pathlib import Path

from pydantic import BaseSettings


project_path = Path(__file__).parent.parent


class Settings(BaseSettings):
    PROJECT_PATH: Path = project_path

    DEBUG: bool = True

    DATABASE_URL: str
    
    AUTH_SECRET: str

    class Config:
        env_file = project_path / '.env'


settings = Settings()  # type: ignore
