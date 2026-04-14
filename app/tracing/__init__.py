# -*- coding: utf-8 -*-
"""
Jaeger分布式追踪配置
"""
import os
import functools
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.trace import SpanKind

# 设置追踪提供者
trace.set_tracer_provider(TracerProvider())

# 创建Jaeger导出器
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",  # Jaeger Agent的主机名
    agent_port=6831,  # Jaeger Agent的端口
)

# 添加批次处理器
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# 初始化Flask追踪

def init_tracer(app):
    """
    初始化分布式追踪
    """
    # 为Flask应用添加追踪
    FlaskInstrumentor().instrument_app(app)
    
    # 为requests库添加追踪
    RequestsInstrumentor().instrument()
    
    return app

# 获取追踪器
def get_tracer(name):
    """
    获取追踪器
    """
    return trace.get_tracer(name)

# 分布式追踪装饰器
def tracing(name=None, kind=SpanKind.INTERNAL):
    """
    分布式追踪装饰器
    
    参数:
        name: 追踪名称，如果不提供则使用函数名
        kind: 追踪类型
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取追踪器
            tracer = get_tracer(func.__module__)
            
            # 创建追踪名称
            span_name = name or func.__name__
            
            # 开始追踪
            with tracer.start_as_current_span(span_name, kind=kind) as span:
                try:
                    # 记录函数参数
                    if args:
                        span.set_attribute("args", str(args))
                    if kwargs:
                        for key, value in kwargs.items():
                            # 避免记录敏感信息
                            if key not in ["password", "secret", "token"]:
                                span.set_attribute(f"kwargs.{key}", str(value))
                    
                    # 执行函数
                    result = func(*args, **kwargs)
                    
                    # 记录结果
                    if result is not None:
                        span.set_attribute("result", str(result)[:1000])  # 限制结果长度
                    
                    return result
                except Exception as e:
                    # 记录异常信息
                    span.record_exception(e)
                    span.set_attribute("error", True)
                    raise
        return wrapper
    return decorator
