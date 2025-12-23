"""
Pydantic models for health check endpoints.

Defines schemas for application health status.
"""
from typing import Optional

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Health status for a single component."""
    
    status: str = Field(
        ...,
        description="Component status: healthy, degraded, or unhealthy"
    )
    
    message: Optional[str] = Field(
        None,
        description="Additional status message"
    )
    
    latency_ms: Optional[float] = Field(
        None,
        description="Response latency in milliseconds"
    )


class HealthResponse(BaseModel):
    """Overall health check response."""
    
    status: str = Field(
        ...,
        description="Overall status: healthy, degraded, or unhealthy"
    )
    
    version: str = Field(
        ...,
        description="Application version"
    )
    
    environment: str = Field(
        ...,
        description="Environment name (development, staging, production)"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "version": "0.1.0",
                    "environment": "development"
                }
            ]
        }
    }


class AzureHealthResponse(BaseModel):
    """Azure services health check response."""
    
    overall_status: str = Field(
        ...,
        description="Overall Azure services status"
    )
    
    azure_openai: HealthStatus = Field(
        ...,
        description="Azure OpenAI service status"
    )
    
    azure_search: HealthStatus = Field(
        ...,
        description="Azure AI Search service status"
    )
    
    ai_foundry: HealthStatus = Field(
        ...,
        description="Azure AI Foundry service status"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "overall_status": "healthy",
                    "azure_openai": {
                        "status": "healthy",
                        "message": "Connected",
                        "latency_ms": 45.2
                    },
                    "azure_search": {
                        "status": "healthy",
                        "message": "Connected",
                        "latency_ms": 23.1
                    },
                    "ai_foundry": {
                        "status": "healthy",
                        "message": "Assistant accessible",
                        "latency_ms": 67.8
                    }
                }
            ]
        }
    }
