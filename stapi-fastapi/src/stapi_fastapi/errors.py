from typing import Any

from fastapi import HTTPException, status


class StapiError(HTTPException):
    pass


class QueryablesError(StapiError):
    def __init__(self, detail: Any) -> None:
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)


class NotFoundError(StapiError):
    def __init__(self, detail: Any | None = None) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail)
