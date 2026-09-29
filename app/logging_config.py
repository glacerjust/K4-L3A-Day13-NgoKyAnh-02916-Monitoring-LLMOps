from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars

from .pii import scrub_text

LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))


class JsonlFileProcessor:
    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        rendered = structlog.processors.JSONRenderer()(logger, method_name, event_dict)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(rendered + "\n")
        return event_dict



def _scrub_value(val: Any) -> Any:
    if isinstance(val, str):
        return scrub_text(val)
    if isinstance(val, dict):
        return {k: _scrub_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_scrub_value(item) for item in val]
    return val


def scrub_event(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    for k, v in list(event_dict.items()):
        if k not in ("ts", "level", "service", "correlation_id"):
            event_dict[k] = _scrub_value(v)
    return event_dict



def configure_logging() -> None:
    logging.basicConfig(format="%(message)s", level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
            scrub_event,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            JsonlFileProcessor(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )



def get_logger() -> structlog.typing.FilteringBoundLogger:
    return structlog.get_logger()
