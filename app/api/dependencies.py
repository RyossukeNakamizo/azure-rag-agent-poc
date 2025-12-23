"""FastAPI Dependencies"""

from typing import Annotated
from fastapi import Depends
from app.core.config import Settings, settings
from app.services.foundry_agent import FoundryAgentService


def get_agent_service(
    settings: Annotated[Settings, Depends(lambda: settings)]
) -> FoundryAgentService:
    """FoundryAgentService 依存性注入"""
    return FoundryAgentService(
        azure_openai_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        azure_openai_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
        api_version=settings.AZURE_OPENAI_API_VERSION
    )


AgentServiceDep = Annotated[FoundryAgentService, Depends(get_agent_service)]
SettingsDep = Annotated[Settings, Depends(lambda: settings)]
