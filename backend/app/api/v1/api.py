from fastapi import APIRouter
from app.api.v1 import auth, users, portfolios, entities, datasources

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(entities.router, tags=["entities"])
api_router.include_router(datasources.router, prefix="/datasources", tags=["datasources"])
