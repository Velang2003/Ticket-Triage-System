"""API v1 router — aggregates all route modules."""
from fastapi import APIRouter

from app.api.v1.tickets import router as tickets_router
from app.api.v1.knowledge_articles import router as articles_router
from app.api.v1.reports import router as reports_router
from app.api.v1.health import router as health_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(tickets_router)
api_v1_router.include_router(articles_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(health_router)
