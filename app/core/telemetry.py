"""
OpenTelemetry Integration - D28 (Lightweight)
"""
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

tracer: Optional[trace.Tracer] = None
_configured = False


def configure_telemetry() -> bool:
    """軽量版OpenTelemetry設定 - ブロッキングを回避"""
    global tracer, _configured
    
    if _configured:
        return True
    
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry disabled")
        return False
    
    if not settings.APPLICATIONINSIGHTS_CONNECTION_STRING:
        logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not set")
        return False
    
    try:
        # リソース定義
        resource = Resource(attributes={
            "service.name": "azure-rag-agent-poc",
            "service.version": "1.0.0"
        })
        
        # TracerProvider設定
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Azure Monitor Exporter（非同期バッチ処理）
        from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
        exporter = AzureMonitorTraceExporter(
            connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING
        )
        
        # BatchSpanProcessor でブロッキング回避
        span_processor = BatchSpanProcessor(
            exporter,
            max_queue_size=2048,
            schedule_delay_millis=5000,  # 5秒ごとに送信
            max_export_batch_size=512
        )
        tracer_provider.add_span_processor(span_processor)
        
        tracer = trace.get_tracer(__name__)
        _configured = True
        logger.info("✅ OpenTelemetry configured (lightweight mode)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to configure OpenTelemetry: {e}")
        # エラーでもサーバー起動は継続
        return False


@contextmanager
def trace_operation(operation_name: str, attributes: Optional[Dict[str, Any]] = None):
    """汎用トレース操作"""
    if tracer is None:
        yield None
        return
    
    with tracer.start_as_current_span(operation_name) as span:
        try:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


@contextmanager
def trace_search_operation(query: str, top_k: int = 5):
    """検索操作のトレース"""
    with trace_operation("search.hybrid", {"search.query": query, "search.top_k": top_k}) as span:
        yield span


@contextmanager  
def trace_openai_operation(operation: str, model: Optional[str] = None):
    """OpenAI操作のトレース"""
    with trace_operation(f"openai.{operation}", {"openai.operation": operation, "openai.model": model or "gpt-4o"}) as span:
        yield span


@contextmanager
def trace_cosmos_operation(operation: str, container: Optional[str] = None):
    """Cosmos DB操作のトレース"""
    with trace_operation(f"cosmos.{operation}", {"cosmos.operation": operation, "cosmos.container": container}) as span:
        yield span
