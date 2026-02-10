"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import example, health, ai_model, prompt_template, prompt_use_case, system_config, test_task, test_execution, evaluation

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(example.router, prefix="/examples", tags=["examples"])
api_router.include_router(ai_model.router, prefix="/ai-models", tags=["ai-models"])
api_router.include_router(prompt_template.router, prefix="/prompt-templates", tags=["prompt-templates"])
api_router.include_router(prompt_use_case.router, prefix="/prompt-use-cases", tags=["prompt-use-cases"])
api_router.include_router(system_config.router, prefix="/system-configs", tags=["system-configs"])
api_router.include_router(test_task.router, prefix="/test-tasks", tags=["test-tasks"])
api_router.include_router(test_execution.router, prefix="/executions", tags=["executions"])
api_router.include_router(evaluation.router, prefix="/evaluations", tags=["evaluations"])

