"""
Tenant Resolver - Multi-tenant Isolation Service
"""

from typing import Optional
from fastapi import Header, HTTPException, status
from jose import JWTError, jwt
import structlog

logger = structlog.get_logger(__name__)


class TenantResolver:
    """Resolves tenant identity from incoming requests."""
    
    def __init__(self, jwt_secret: Optional[str] = None, jwt_algorithm: str = "HS256"):
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        logger.info("tenant_resolver_initialized", jwt_enabled=bool(jwt_secret))
    
    def get_tenant_id_from_header(
        self,
        x_tenant_id: Optional[str] = Header(None, description="Tenant ID")
    ) -> str:
        if not x_tenant_id:
            logger.warning("missing_tenant_id_header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Tenant-ID header is required"
            )
        
        if not self._is_valid_tenant_id(x_tenant_id):
            logger.warning("invalid_tenant_id_format", tenant_id=x_tenant_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant_id format"
            )
        
        logger.info("tenant_resolved_from_header", tenant_id=x_tenant_id)
        return x_tenant_id
    
    def get_tenant_id_from_token(
        self,
        authorization: Optional[str] = Header(None, description="JWT Bearer token")
    ) -> str:
        if not authorization:
            logger.warning("missing_authorization_header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header is required"
            )
        
        if not authorization.startswith("Bearer "):
            logger.warning("invalid_authorization_format")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization format"
            )
        
        token = authorization.replace("Bearer ", "")
        
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                logger.warning("missing_tenant_id_in_token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token does not contain tenant_id claim"
                )
            
            logger.info("tenant_resolved_from_token", tenant_id=tenant_id)
            return tenant_id
            
        except JWTError as e:
            logger.error("jwt_validation_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    def _is_valid_tenant_id(self, tenant_id: str) -> bool:
        import re
        
        if not tenant_id or len(tenant_id) < 3 or len(tenant_id) > 64:
            return False
        
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$'
        return bool(re.match(pattern, tenant_id))


def get_tenant_id(
    x_tenant_id: Optional[str] = Header(None),
    resolver: TenantResolver = None
) -> str:
    if resolver is None:
        resolver = TenantResolver()
    
    return resolver.get_tenant_id_from_header(x_tenant_id)
