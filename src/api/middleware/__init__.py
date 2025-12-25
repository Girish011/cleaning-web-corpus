"""
API middleware package.
"""

from src.api.middleware.error_handler import error_handler_middleware

__all__ = ["error_handler_middleware"]

