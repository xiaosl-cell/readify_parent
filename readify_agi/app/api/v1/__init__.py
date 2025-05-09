from fastapi import APIRouter
from app.api.v1 import agent_router

api_router = APIRouter()
api_router.include_router(agent_router.router, prefix="/agent", tags=["agent"])