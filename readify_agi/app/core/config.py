from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """应用配置"""
    # 数据库配置
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    
    # 向量存储配置
    VECTOR_STORE_DIR: str = "data/vector_store"
    
    # Chroma配置
    CHROMA_SERVER_HOST: str = "localhost"
    CHROMA_SERVER_PORT: int = 8000
    CHROMA_SERVER_SSL_ENABLED: bool = False
    
    # LlamaParse配置
    LLAMA_PARSE_API_KEY: str
    
    # OpenAI配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "")
    
    # OpenAI-国内专线
    OPENAI_API_KEY_CHINA: str = os.getenv("OPENAI_API_KEY_CHINA", "")
    OPENAI_API_BASE_CHINA: str = os.getenv("OPENAI_API_BASE_CHINA", "")
    
    # Qwen
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    QWEN_API_BASE: str = os.getenv("QWEN_API_BASE", "")

    # 回调配置
    FILE_PROCESS_CALLBACK_URL: str = os.getenv("FILE_PROCESS_CALLBACK_URL", "")
    FILE_PROCESS_CALLBACK_API_KEY: str = os.getenv("FILE_PROCESS_CALLBACK_API_KEY", "")
    
    # SerpAPI配置
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
    
    # 数据库连接URL
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4&use_unicode=1"
            "&auth_plugin=caching_sha2_password"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 