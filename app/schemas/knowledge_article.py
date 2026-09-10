"""Knowledge article request/response schemas."""
from pydantic import BaseModel, Field


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1)
    category: str | None = Field(
        None,
        description="One of: Billing, Technical, Account, Other",
    )


class ArticleUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    content: str | None = Field(None, min_length=1)
    category: str | None = None


class ArticleResponse(BaseModel):
    id: str
    title: str
    content: str
    category: str | None
    created_at: str
    updated_at: str

