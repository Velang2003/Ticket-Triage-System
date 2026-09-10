"""Report response schema."""

from pydantic import BaseModel


class ReportSummaryResponse(BaseModel):
    total: int
    by_category: dict[str, int]
    by_priority: dict[str, int]
    by_status: dict[str, int]
    from_date: str | None
    to_date: str | None
