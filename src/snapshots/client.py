import base64
import copy
import datetime
import mimetypes
from typing import Any
from urllib.parse import urlparse, urlunparse, urljoin

import minify_html
import requests
from babel.dates import format_date
from babel.support import Translations
from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape

from src.config import settings
from src.database import get_db_session
from src.mirrors.service import resolve_mirror
from src.pangea.client import pangea_expanded_image_url
from src.snapshots.config import SnapshotsConfig, config_for_url
from src.snapshots.schemas import SnapshotContext
from src.snapshots.service import resolve_snapshot


class SnapshotParseError(RuntimeError):
    pass


ALLOWED_ASSET_TYPES = {
    "image/jpeg",
    "image/webp",
    "image/png",
    "image/gif",
    "image/svg+xml",
    "image/x-icon",
}


def encode_data_uri(content: bytes, content_type: str) -> str | None:
    content_type = content_type.split(";")[0].strip().lower()
    if content_type not in ALLOWED_ASSET_TYPES:
        return None
    encoded = base64.b64encode(content).decode("utf-8")
    return f"data:{content_type};base64,{encoded}"


def fetch_file(filename: str) -> str | None:
    content_type = mimetypes.guess_type(filename)[0]
    if content_type not in ALLOWED_ASSET_TYPES:
        return None
    try:
        with open(filename, "rb") as f:
            return encode_data_uri(f.read(), content_type)
    except IOError:
        return None


def fetch_url(base: str, url: str) -> str | None:
    if url.startswith("data:"):
        return url
    url = urljoin(base, url)
    try:
        response = requests.get(url, stream=True, timeout=0.5)
        response.raise_for_status()
        content_length = response.headers.get("Content-Length")
        if content_length is not None:
            try:
                if int(content_length) > 500_000:
                    return None
            except ValueError:
                pass  # Invalid Content-Length format, proceed to stream
        content = b""
        for chunk in response.iter_content(chunk_size=1024):
            content += chunk
            if len(content) > 500_000:
                return None
        content_type = response.headers.get("Content-Type", "")
        return encode_data_uri(content, content_type)
    except requests.exceptions.RequestException:
        return None


class SnapshotCamera:
    config: SnapshotsConfig | None = None
    context: SnapshotContext | None = None
    raw: bytes | None = None
    soup: BeautifulSoup | None = None

    def __init__(self, url: str) -> None:
        self.url = url
        self.config = config_for_url(url)

    def get_content(self) -> None:
        self.raw = requests.get(self.url, timeout=1).content

    def _get_attribute_value(self, selector: str, attribute: str) -> str | None:
        element = self.soup.select_one(selector)
        if not element:
            return None
        try:
            return element[attribute]
        except KeyError:
            return None

    def get_attribute_value(
        self, selector: str | list[str] | None, attribute: str, optional: bool = False
    ) -> str | None:
        if not selector:
            if optional:
                return None
            raise SnapshotParseError("No selector specified for non-optional attribute")
        if isinstance(selector, str):
            selector = [selector]
        for s in selector:
            if result := self._get_attribute_value(s, attribute):
                return result
        if optional:
            return None
        raise SnapshotParseError("No element matched for non-optional attribute")

    def get_element_content(
        self, selector: str | None, optional: bool = False
    ) -> str | None:
        if not selector:
            if optional:
                return None
            raise SnapshotParseError("No selector specified for non-optional element")
        element = self.soup.select_one(selector)
        if not element:
            if not optional:
                raise SnapshotParseError(f"Missing element for selector: {selector}")
            return None
        return element.text

    def _get_opengraph_value(self, prop: str) -> str | None:
        element = self.soup.select_one(f'meta[name="{prop}"]')
        if not element:
            return None
        try:
            return element["content"]
        except KeyError:
            return None

    def get_opengraph_value(
        self, prop: str | list[str] | None, optional: bool = False
    ) -> str | None:
        if not prop:
            if optional:
                return None
            raise SnapshotParseError("No property specified for non-optional property")
        if isinstance(prop, str):
            prop = [prop]
        for p in prop:
            if result := self._get_opengraph_value(p):
                return result
        if optional:
            return None
        raise SnapshotParseError("No property matched for non-optional property")

    def get_body(self):
        body = copy.copy(self.soup.select_one(self.config.article_body_selector))
        if self.config.article_body_remove_selector:
            for element in body.select(", ".join(self.config.article_body_remove_selector)):
                element.decompose()
        for image in body.select("img"):
            image.attrs = {
                "src": fetch_url(
                    pangea_expanded_image_url(self.url),
                    image.get("src", image.get("data-src", "")),
                ),
                "alt": image.get("alt", ""),
            }
        with get_db_session() as db:
            for hyperlink in body.select("a"):
                absolute_url = urljoin(self.url, hyperlink.get("href"))
                existing_snapshot = resolve_snapshot(db, absolute_url)
                if existing_snapshot:
                    hyperlink.attrs.update(
                        {"href": existing_snapshot, "class": "snap-link--snapshot"}
                    )
                    continue
                mirror_url = resolve_mirror(db, absolute_url)
                if mirror_url:
                    hyperlink.attrs.update(
                        {"href": mirror_url, "class": "snap-link--mirror"}
                    )
                    continue
                hyperlink.attrs.update({"href": absolute_url})

        return str(body)

    def preprocess(self) -> None:
        compound = ", ".join(
            self.config.pre_remove_selectors + ["form", "script", "style", "iframe"]
        )
        for element in self.soup.select(compound):
            element.decompose()
        for element in self.soup.select("[style]"):
            element.attrs.pop("style")

    def favicon(self):
        favicon_src = self.get_attribute_value('link[rel="icon"]', "href", optional=True)
        if favicon_src:
            icon = fetch_url(self.url, favicon_src)
            return icon
        parsed = urlparse(self.url)
        icon_url = urlunparse((parsed.scheme, parsed.netloc, "/favicon.ico", "", "", ""))
        return fetch_url(self.url, icon_url)

    def published_time(self, locale) -> str:
        if self.config.article_published_selector:
            if published := self.get_element_content(
                self.config.article_published_selector, optional=True
            ):
                return published
        ts = datetime.datetime.fromisoformat(
            self.get_opengraph_value("article:published_time")
        )
        return format_date(ts, locale=locale)

    def parse(self) -> None:
        if not self.config:
            self.config = config_for_url(self.url)
        if not self.config:
            return
        self.soup = BeautifulSoup(self.raw, "lxml")
        self.preprocess()
        if self.config.article_image_selector:
            article_image_source = self.get_attribute_value(
                self.config.article_image_selector, "src"
            )
            article_image_source = pangea_expanded_image_url(article_image_source)
        else:
            article_image_source = None
        page_language = self.get_attribute_value(["html", "body"], "lang", optional=True)
        site_url = urlunparse(urlparse(self.url)._replace(path="/"))
        with get_db_session() as db:
            article_mirror_url = resolve_mirror(db, self.url)
        site_mirror_url = (
            urlunparse(urlparse(article_mirror_url)._replace(path="/"))
            if article_mirror_url
            else None
        )
        self.context = SnapshotContext(
            article_author=self.get_element_content(
                self.config.article_author_selector, optional=True
            ),
            article_body=self.get_body(),
            article_description=self.get_attribute_value(
                'meta[name="description"]', "content", optional=True
            ),
            article_image=(
                fetch_url(self.url, article_image_source) if article_image_source else None
            ),
            article_image_caption=self.get_element_content(
                self.config.article_image_caption_selector, optional=True
            ),
            article_image_source=article_image_source,
            article_published=self.published_time(page_language),
            article_title=self.get_element_content(self.config.article_title_selector),
            article_url=self.url,
            article_mirror_url=article_mirror_url,
            matomo_host=settings.MATOMO_HOST,
            matomo_site_id=settings.MATOMO_SITE_ID,
            page_direction=self.get_attribute_value(["html", "body"], "dir", optional=True),
            page_language=page_language,
            site_favicon=self.favicon(),
            site_logo=fetch_file(self.config.site_logo),
            site_title=self.config.site_title,
            site_url=site_url,
            site_mirror_url=site_mirror_url,
        )

    def get_context(self) -> dict[str, Any] | None:
        self.config = config_for_url(self.url)
        if self.config:
            self.get_content()
            self.parse()
            return self.context.model_dump()
        return None

    def render(self) -> str:
        context = self.get_context()
        jinja_env = Environment(
            loader=PackageLoader(
                package_name="src.snapshots",
                package_path="templates",
            ),
            extensions=["jinja2.ext.i18n"],
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        translations = Translations.load("i18n", [context["page_language"], "en"])
        jinja_env.install_gettext_translations(translations)
        template = jinja_env.get_template("article-template.html.j2")
        return minify_html.minify(
            template.render(**context), minify_js=True, minify_css=True
        )
