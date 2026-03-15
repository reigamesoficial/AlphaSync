from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    clients,
    companies,
    company,
    conversations,
    dashboard,
    measures,
    quotes,
    users,
    webhook,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(companies.router)
api_router.include_router(company.router)
api_router.include_router(clients.router)
api_router.include_router(conversations.router)
api_router.include_router(quotes.router)
api_router.include_router(dashboard.router)
api_router.include_router(measures.router)
api_router.include_router(webhook.router)
