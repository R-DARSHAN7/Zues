from urllib.parse import quote_plus
from pydantic import model_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    owner_name: str = "Boss"
    openai_api_key: str = ""
    use_ollama: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    supabase_host: str = ""
    supabase_port: int = 5432
    supabase_user: str = "postgres"
    supabase_password: str = ""
    supabase_db: str = "postgres"
    audio_ttl_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @computed_field
    @property
    def database_url(self) -> str:
        encoded_password = quote_plus(self.supabase_password)
        return f"postgresql+asyncpg://{self.supabase_user}:{encoded_password}@{self.supabase_host}:{self.supabase_port}/{self.supabase_db}"
settings = Settings()