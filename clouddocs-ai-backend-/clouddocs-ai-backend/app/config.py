from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    supabase_url: str
    supabase_service_key: str
    supabase_storage_bucket: str = "clouddocs-ai"

    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"

    chroma_persist_dir: str = "./chroma_data"

    max_upload_size_mb: int = 10
    cors_origins: str = "*"

    class Config:
        env_file = ".env"


settings = Settings()
