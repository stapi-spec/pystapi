from fastapi.datastructures import URL
from stapi_pydantic import Link

from stapi_fastapi.constants import TYPE_JSON


def json_link(rel: str, href: URL) -> Link:
    return Link(href=href, rel=rel, type=TYPE_JSON)
