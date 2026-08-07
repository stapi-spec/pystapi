from typing import Any

from fastapi import HTTPException, status


class StapiError(HTTPException):
    pass


class QueryablesError(StapiError):
    def __init__(self, detail: Any) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)


class NotFoundError(StapiError):
    def __init__(self, detail: Any | None = None) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class PaginationTokenError(ValueError):
    """Returned by a backend, inside a `Failure`, when a pagination token
    identifies no page. The handler answers it with a 404.

    Not an `HTTPException`: a backend reports it rather than raises it. Its own
    type, rather than a bare `ValueError`, because a backend raises those
    incidentally -- an `int()` on unparseable input, a `list.index` miss on
    something other than the token -- and every one of them would otherwise be
    reported to the client as a page that does not exist.
    """
