import urllib


def urljoin(href: str, name: str) -> str:
    """Joins a path onto an existing href, respecting query strings, etc."""
    url = urllib.parse.urlparse(href)
    path = url.path
    if not path.endswith("/"):
        path += "/"
    return urllib.parse.urlunparse(url._replace(path=path + name))
