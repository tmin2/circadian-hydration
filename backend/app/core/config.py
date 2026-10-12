"""
Circadian Hydration Platform - 핵심 애플리케이션 환경 설정 모듈
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 전역 설정 클래스"""

    PROJECT_NAME: str = "Circadian Hydration Platform API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL 데이터베이스 연결 URL (기본 로컬 접속 주소 설정)
    # 비동기 연결을 위해 postgresql+asyncpg 형태 지원
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/circadian_hydration"
    # 동기식 마이그레이션 및 세션용 URL
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/circadian_hydration"

    # JWT 인증 비밀키 및 알고리즘
    SECRET_KEY: str = "circadian_secret_jwt_key_hydration_platform_2026_mvp"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일

    # CORS 허용 오리진 목록
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "*",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
