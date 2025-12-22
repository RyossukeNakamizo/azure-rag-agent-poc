"""Chat API endpoints"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from app.api.dependencies import AgentServiceDep

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    query: str
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str


@router.post("/chat")
async def chat(
    request: ChatRequest,
    agent_service: AgentServiceDep
):
    """Chat with the agent"""
    if request.stream:
        async def generate():
            async for chunk in agent_service.chat_stream(request.query):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    else:
        response = await agent_service.chat(request.query)
        return {"response": response}
