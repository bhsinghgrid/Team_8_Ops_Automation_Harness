"""
Structured logging configuration for the Shadow Agent.
"""
import logging.config
import json
import os
from logging import Formatter

class JsonFormatter(Formatter):
    """Formats log records as JSON."""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # If the log message is a dict and has 'json_fields', merge it
        if isinstance(record.msg, dict) and getattr(record, 'json_fields', False):
            log_record.update(record.msg)
        else:
            log_record["message"] = record.getMessage()

        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging(log_dir: str = "logs", log_level: str = "INFO"):
    """
    Set up structured JSON logging for the application.
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "shadow_agent_framework.utils.logging_config.JsonFormatter",
            },
        },
        "handlers": {
            "console": {
                "level": log_level,
                "class": "logging.StreamHandler",
            },
            "file": {
                "level": log_level,
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": os.path.join(log_dir, "shadow_agent.log.json"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"],
        },
    }
    logging.config.dictConfig(log_config)
    logging.info("Structured logging initialized.")
