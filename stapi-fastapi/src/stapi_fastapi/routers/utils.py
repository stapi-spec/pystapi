from stapi_pydantic import Link
from starlette.datastructures import URL

from stapi_fastapi.constants import TYPE_JSON


def json_link(href: URL, rel: str) -> Link:
    return Link(
        href=str(href),
        rel=rel,
        type=TYPE_JSON,
    )
