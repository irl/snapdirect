from os.path import abspath, dirname, join
from typing import Any

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    YamlConfigSettingsSource,
    PydanticBaseSettingsSource,
)

from src.constants import Environment

API_README_PATH = abspath(join(dirname(__file__), "API.md"))

with open(API_README_PATH, "r", encoding="utf-8") as f:
    API_README_MD = f.read()


class CustomBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        yaml_file="config.yaml", yaml_file_encoding="utf-8", extra="ignore"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (YamlConfigSettingsSource(settings_cls),)


class Config(CustomBaseSettings):
    # DATABASE_URL: PostgresDsn
    # DATABASE_ASYNC_URL: PostgresDsn
    # DATABASE_POOL_SIZE: int = 16
    # DATABASE_POOL_TTL: int = 60 * 20  # 20 minutes
    # DATABASE_POOL_PRE_PING: bool = True

    ENVIRONMENT: Environment = Environment.PRODUCTION

    CORS_ORIGINS: list[str] = ["*"]
    CORS_ORIGINS_REGEX: str | None = None
    CORS_HEADERS: list[str] = ["*"]

    APP_VERSION: str = "0.0.0"


settings = Config()

app_configs: dict[str, Any] = {
    "title": "snapdirect",
    "version": settings.APP_VERSION,
    "description": API_README_MD,
}

if not settings.ENVIRONMENT.is_debug:
    app_configs["openapi_url"] = None  # hide docs
