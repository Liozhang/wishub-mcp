"""
结构化日志配置
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """添加应用上下文信息"""
    event_dict["app"] = "wishub-mcp"
    return event_dict


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """
    配置结构化日志

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: 是否使用 JSON 格式
    """
    # 配置标准库 logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    # 配置 structlog 处理器
    processors: list[Processor] = [
        # 添加时间戳
        structlog.processors.TimeStamper(fmt="iso"),
        # 添加日志级别
        structlog.stdlib.add_log_level,
        # 添加应用上下文
        add_app_context,
        # 添加调用者信息（仅在 DEBUG 模式）
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ) if log_level.upper() == "DEBUG" else lambda logger, method_name, event_dict: event_dict,
        # 异常信息格式化
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # 根据格式选择输出处理器
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # 配置 structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    获取结构化日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        BoundLogger 实例
    """
    return structlog.get_logger(name)
