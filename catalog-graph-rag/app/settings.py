from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_GPT4O_DEPLOYMENT: str

    AZURE_COHERE_API_KEY: str
    AZURE_COHERE_ENDPOINT: str
    AZURE_COHERE_DEPLOYMENT: str
    AZURE_COHERE_EMBED_DIM: int

    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    CHUNK_CHARS: int = 1400
    CHUNK_OVERLAP: int = 120
    MAX_EMBED_CHARS: int = 8000
    TOP_K: int = 8
