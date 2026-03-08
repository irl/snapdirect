import fnmatch

from pydantic import BaseModel, Field

from src.config import CustomBaseSettings


class SnapshotsConfig(BaseModel):
    article_author_selector: str | None = None
    article_image_selector: str | None = None
    article_image_caption_selector: str | None = None
    article_body_selector: str
    article_body_remove_selector: list[str] = []
    article_published_selector: str | None = Field(
        None,
        description="CSS selector for an element containing a localised publication datetime. By default, the publication date will be determined from the OpenGraph metadata.",
    )
    article_title_selector: str = "h1"
    match_urls: list[str]
    pre_remove_selectors: list[str] = "aside"
    site_logo: str
    site_title: str


class Config(CustomBaseSettings):
    PARSER_CONFIGS: list[SnapshotsConfig]


settings = Config()


def config_for_url(url: str) -> SnapshotsConfig | None:
    for cfg in settings.PARSER_CONFIGS:
        for pattern in cfg.match_urls:
            if fnmatch.fnmatch(url, pattern):
                return cfg
    return None
