from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SpeakScene API"
    database_url: str = "sqlite:///./speakscene.db"
    ai_provider: str = "openai"
    openai_api_key: str | None = "sk-cp-9SX3RaY-EKOLupMi3ChYaogOhRQ2B9h4d0-dn9XEva42n5Qx52ojbe_FOAA3AYa5ojMlFNrSU7yWczFLHqo-Zm2CQiYG5TppD_rrIb7rDmftXki58H18mZE"
    openai_base_url: str | None = "https://api.minimaxi.com/v1"
    openai_model: str = "MiniMax-M2.7"
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"
    elevenlabs_model_id: str = "eleven_v3"
    elevenlabs_output_format: str = "mp3_44100_128"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
