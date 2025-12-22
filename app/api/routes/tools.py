from fastapi import APIRouter
from app.models.chat import ToolInfo
from app.api.dependencies import AgentServiceDep
from typing import List

router = APIRouter()

@router.get("/tools", response_model=List[ToolInfo])
async def list_tools(agent_service: AgentServiceDep) -> List[ToolInfo]:
    tools = agent_service.get_available_tools()
    return [
        ToolInfo(
            name=tool.get("name", tool.get("type", "unknown")),
            description=tool.get("description", ""),
            parameters=tool.get("parameters", {})
        )
        for tool in tools
    ]
