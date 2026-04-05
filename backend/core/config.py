from urllib.parse import quote_plus
from pydantic import model_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    owner_name: str = "Boss"

    # LLM
    openai_api_key: str = ""
    use_ollama: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # TTS
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"

    # Supabase
    supabase_host: str = ""
    supabase_port: int = 5432
    supabase_user: str = "postgres"
    supabase_password: str = ""
    supabase_db: str = "postgres"

    # Audio
    audio_ttl_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @computed_field
    @property
    def database_url(self) -> str:
        encoded_password = quote_plus(self.supabase_password)
        return (
            f"postgresql+asyncpg://"
            f"{self.supabase_user}:{encoded_password}"
            f"@{self.supabase_host}:{self.supabase_port}"
            f"/{self.supabase_db}"
        )

    @model_validator(mode="after")
    def validate_required(self) -> "Settings":
        errors = []

        if not self.supabase_host:
            errors.append(
                "SUPABASE_HOST is missing. "
                "Get it from Supabase → Settings → Database → Host"
            )

        if not self.supabase_password:
            errors.append(
                "SUPABASE_PASSWORD is missing. "
                "This is the password you set when creating your Supabase project."
            )

        if not self.use_ollama and not self.openai_api_key:
            errors.append(
                "OPENAI_API_KEY is missing and USE_OLLAMA is false. "
                "Either set your OpenAI key or set USE_OLLAMA=true"
            )

        if self.use_ollama and not self.ollama_url:
            errors.append(
                "USE_OLLAMA is true but OLLAMA_URL is not set."
            )

        if errors:
            msg = "\n\nZEUS config errors:\n" + "\n".join(
                f"  x {e}" for e in errors
            )
            raise ValueError(msg)

        return self


settings = Settings()