"""Shared response models."""

from pydantic import BaseModel


class PaginatedResponse[T](BaseModel):
    data: list[T]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    detail: str
    code: str
