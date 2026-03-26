from pydantic import BaseModel


class SnapshotContext(BaseModel):
    article_author: str | None = None
    article_body: str
    article_description: str | None = None
    article_image: str | None = None
    article_image_caption: str | None = None
    article_image_source: str | None = None
    article_published: str
    article_title: str
    article_url: str
    article_mirror_url: str | None = None
    matomo_host: str
    matomo_site_id: int
    page_direction: str | None = None
    page_language: str | None = None
    site_favicon: str | None = None
    site_logo: str = None
    site_title: str
    site_mirror_url: str | None = None
    site_url: str
