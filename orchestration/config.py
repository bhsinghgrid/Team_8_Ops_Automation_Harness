# src/runbook_pipeline/config.py
"""
Configuration management for the runbook pipeline.
In a production system, this would load from a file or environment variables.
"""
import logging

def get_logger(name: str):
    """Returns a configured logger instance."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    return logging.getLogger(name)
