"""
OData Filter Builder - Safe Filter Construction for Azure AI Search
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import structlog

logger = structlog.get_logger(__name__)


class FilterBuilder:
    """Builds OData filter expressions for Azure AI Search."""
    
    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.filters: List[str] = []
        
        if tenant_id:
            self.add_tenant_filter(tenant_id)
            logger.info("filter_builder_initialized", tenant_id=tenant_id)
    
    def add_tenant_filter(self, tenant_id: str) -> "FilterBuilder":
        sanitized_id = self._sanitize_string(tenant_id)
        self.filters.append(f"tenant_id eq '{sanitized_id}'")
        logger.debug("tenant_filter_added", tenant_id=tenant_id)
        return self
    
    def add_equals(self, field: str, value: Any) -> "FilterBuilder":
        self._validate_field_name(field)
        encoded_value = self._encode_value(value)
        self.filters.append(f"{field} eq {encoded_value}")
        logger.debug("equals_filter_added", field=field, value=value)
        return self
    
    def add_not_equals(self, field: str, value: Any) -> "FilterBuilder":
        self._validate_field_name(field)
        encoded_value = self._encode_value(value)
        self.filters.append(f"{field} ne {encoded_value}")
        logger.debug("not_equals_filter_added", field=field, value=value)
        return self
    
    def add_greater_than(self, field: str, value: Any) -> "FilterBuilder":
        self._validate_field_name(field)
        encoded_value = self._encode_value(value)
        self.filters.append(f"{field} gt {encoded_value}")
        return self
    
    def add_less_than(self, field: str, value: Any) -> "FilterBuilder":
        self._validate_field_name(field)
        encoded_value = self._encode_value(value)
        self.filters.append(f"{field} lt {encoded_value}")
        return self
    
    def add_in(self, field: str, values: List[Any]) -> "FilterBuilder":
        if not values:
            logger.warning("empty_values_for_in_filter", field=field)
            return self
        
        self._validate_field_name(field)
        encoded_values = [self._encode_value(v) for v in values]
        values_str = ", ".join(encoded_values)
        self.filters.append(f"search.in({field}, '{values_str}', ',')")
        return self
    
    def add_date_range(
        self,
        field: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> "FilterBuilder":
        self._validate_field_name(field)
        
        if start:
            start_str = start.isoformat() + 'Z'
            self.filters.append(f"{field} ge {start_str}")
        
        if end:
            end_str = end.isoformat() + 'Z'
            self.filters.append(f"{field} le {end_str}")
        
        logger.debug("date_range_filter_added", field=field, start=start, end=end)
        return self
    
    def build(self) -> Optional[str]:
        if not self.filters:
            return None
        
        filter_str = " and ".join(self.filters)
        logger.info("filter_built", filter=filter_str, filter_count=len(self.filters))
        return filter_str
    
    def reset(self) -> "FilterBuilder":
        self.filters.clear()
        if self.tenant_id:
            self.add_tenant_filter(self.tenant_id)
        return self
    
    def _validate_field_name(self, field: str) -> None:
        if not re.match(r'^[a-zA-Z0-9_/]+$', field):
            logger.error("invalid_field_name", field=field)
            raise ValueError(f"Invalid field name: {field}")
    
    def _sanitize_string(self, value: str) -> str:
        return value.replace("'", "''")
    
    def _encode_value(self, value: Any) -> str:
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, datetime):
            return value.isoformat() + 'Z'
        elif isinstance(value, str):
            sanitized = self._sanitize_string(value)
            return f"'{sanitized}'"
        else:
            sanitized = self._sanitize_string(str(value))
            return f"'{sanitized}'"


def create_tenant_filter(tenant_id: str, additional_filters: Optional[Dict[str, Any]] = None) -> str:
    builder = FilterBuilder(tenant_id)
    
    if additional_filters:
        for field, value in additional_filters.items():
            builder.add_equals(field, value)
    
    return builder.build()
