import secrets

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_HOST: str = "localhost"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: SecretStr = SecretStr("postgres")
    DATABASE_NAME: str = "postgres"
    DATABASE_PORT: int = 5432
    DATABASE_URI: PostgresDsn | None = None

    @model_validator(mode="before")
    def parse_db_uri(cls, values) -> "DatabaseConfig":
        values["DATABASE_URI"] = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values["DATABASE_USER"],
            password=values["DATABASE_PASSWORD"],
            host=values["DATABASE_HOST"],
            path=values["DATABASE_NAME"],
            port=int(values["DATABASE_PORT"]),
        )
        return values


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: SecretStr = SecretStr("redis")
    REDIS_URI: RedisDsn | None = None

    @model_validator(mode="before")
    def parse_redis_uri(cls, values) -> "RedisConfig":
        values["REDIS_URI"] = RedisDsn.build(
            scheme="redis",
            host=values["REDIS_HOST"],
            port=int(values["REDIS_PORT"]),
            password=values["REDIS_PASSWORD"],
        )
        return values


class AuthConfig(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    JWT_SECRET_KEY: SecretStr = SecretStr(secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


class Config(BaseSettings):

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Bookstore"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    CORS_ORIGINS: List[AnyHttpUrl] = []

    RATE_LIMITER_ENABLED: bool = False
    RATE_LIMITER_MAX_REQUESTS: int = 100
    RATE_LIMITER_TIMEFRAME: int = 60

    auth: AuthConfig = AuthConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    

@lru_cache
def get_config() -> Config:
    return Config()

config = get_config()
