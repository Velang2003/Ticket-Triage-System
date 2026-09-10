"""Ticket request/response Pydantic schemas."""
from typing import Any
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import get_settings

settings = get_settings()


class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200, description="Short ticket title")
    description: str = Field(..., min_length=1, description="Full ticket body")
    submitter_email: EmailStr = Field(..., description="Contact email of the submitter")

    @field_validator("subject")
    @classmethod
    def subject_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("subject cannot be blank")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_length(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("description cannot be blank")
        if len(v) > settings.ticket_description_max_len:
            raise ValueError(
                f"description exceeds maximum length of {settings.ticket_description_max_len} characters"
            )
        return v


class StatusUpdate(BaseModel):
    status: str = Field(..., description="New status: Open | In Progress | Resolved | Closed")

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"Open", "In Progress", "Resolved", "Closed"}
        if v not in allowed:
            raise ValueError(f"status must be one of: {sorted(allowed)}")
        return v


class ClassificationOut(BaseModel):
    id: str
    predicted_category: str | None
    predicted_priority: str | None
    confidence_note: str | None
    is_pending: bool
    created_at: str


class SuggestionOut(BaseModel):
    id: str
    suggested_text: str
    source_article_ids: list[str]
    created_at: str


class TicketResponse(BaseModel):
    id: str
    subject: str
    description: str
    submitter_email: str
    category: str | None
    priority: str | None
    status: str
    created_at: str
    updated_at: str
    classification: ClassificationOut | None = None
    suggestion: SuggestionOut | None = None


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int
    page: int
    page_size: int
    pages: int
