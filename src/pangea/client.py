import re
from urllib.parse import urlparse, urlunparse


def pangea_expanded_image_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.startswith("gdb.") and parsed.path.endswith(".jpg"):
        path = re.sub(r"_w[0-9]+_", "_w600_", parsed.path)
        return urlunparse(parsed._replace(path=path))
    return url
