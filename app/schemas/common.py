"""Common response envelope — SRS §5.1."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: str
    message: str


class ResponseEnvelope(BaseModel, Generic[DataT]):
    """Standard JSON envelope wrapping all API responses."""

    status: str  # "success" or "error"
    data: DataT | None = None
    error: ErrorDetail | None = None

    @classmethod
    def success(cls, data: Any) -> "ResponseEnvelope":
        return cls(status="success", data=data)

    @classmethod
    def error(cls, code: str, message: str) -> "ResponseEnvelope":  # noqa: F811
        return cls(status="error", error=ErrorDetail(code=code, message=message))
