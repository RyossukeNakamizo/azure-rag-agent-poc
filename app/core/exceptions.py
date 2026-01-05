"""
Custom Exceptions

D27: エラーハンドリング強化 - カスタム例外定義
"""
from typing import Optional


class RAGPOCBaseException(Exception):
    """Base exception for RAG POC application"""
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause
        super().__init__(self.message)
    
    def __str__(self):
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message


# =============================================================================
# Cosmos DB Exceptions
# =============================================================================

class CosmosDBError(RAGPOCBaseException):
    """Base exception for Cosmos DB operations"""
    pass


class CosmosDBConnectionError(CosmosDBError):
    """Raised when Cosmos DB connection fails"""
    
    def __init__(self, endpoint: str, cause: Optional[Exception] = None):
        message = f"Failed to connect to Cosmos DB: {endpoint}"
        self.endpoint = endpoint
        super().__init__(message, cause)


class CosmosDBOperationError(CosmosDBError):
    """Raised when Cosmos DB operation fails"""
    
    def __init__(self, operation: str, cause: Optional[Exception] = None):
        message = f"Cosmos DB operation failed: {operation}"
        self.operation = operation
        super().__init__(message, cause)


class CosmosDBNotAvailableError(CosmosDBError):
    """Raised when Cosmos DB is not available (disabled or unreachable)"""
    
    def __init__(self, reason: str = "Cosmos DB is not available"):
        super().__init__(reason)


# =============================================================================
# Search Exceptions
# =============================================================================

class SearchError(RAGPOCBaseException):
    """Base exception for Search operations"""
    pass


class SearchConnectionError(SearchError):
    """Raised when Search service connection fails"""
    
    def __init__(self, endpoint: str, cause: Optional[Exception] = None):
        message = f"Failed to connect to Search service: {endpoint}"
        self.endpoint = endpoint
        super().__init__(message, cause)


class SearchOperationError(SearchError):
    """Raised when Search operation fails"""
    
    def __init__(self, operation: str, cause: Optional[Exception] = None):
        message = f"Search operation failed: {operation}"
        self.operation = operation
        super().__init__(message, cause)


# =============================================================================
# OpenAI Exceptions
# =============================================================================

class OpenAIError(RAGPOCBaseException):
    """Base exception for OpenAI operations"""
    pass


class OpenAIConnectionError(OpenAIError):
    """Raised when OpenAI service connection fails"""
    
    def __init__(self, endpoint: str, cause: Optional[Exception] = None):
        message = f"Failed to connect to OpenAI service: {endpoint}"
        self.endpoint = endpoint
        super().__init__(message, cause)


class OpenAIOperationError(OpenAIError):
    """Raised when OpenAI operation fails"""
    
    def __init__(self, operation: str, cause: Optional[Exception] = None):
        message = f"OpenAI operation failed: {operation}"
        self.operation = operation
        super().__init__(message, cause)
