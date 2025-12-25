"""
API error handling middleware.

Maps exceptions to standardized error response format and status codes
as defined in docs/API_DESIGN.md.
"""

import logging
import uuid
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.schemas.workflow import ErrorResponse

logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    """
    Get or generate request ID from request headers or generate new one.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request ID string
    """
    # Check for X-Request-ID header
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = f"req-{uuid.uuid4().hex[:8]}"
    return request_id


async def error_handler_middleware(request: Request, call_next: Callable) -> JSONResponse:
    """
    Global error handling middleware.
    
    Catches all exceptions and formats them according to API_DESIGN.md
    error response format.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in chain
        
    Returns:
        JSONResponse with error details
    """
    request_id = get_request_id(request)

    try:
        response = await call_next(request)
        return response

    except RequestValidationError as e:
        # 422: Validation error (Pydantic validation)
        logger.warning(f"Validation error: {e.errors()}")
        error_detail = {
            "error": "validation_error",
            "message": "Request validation failed",
            "details": {
                "errors": e.errors(),
            },
            "request_id": request_id,
        }
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_detail,
        )

    except HTTPException as e:
        # HTTP exceptions from route handlers
        # Check if detail is already in error response format
        if isinstance(e.detail, dict) and "error" in e.detail:
            # Already formatted, just ensure request_id is present
            if "request_id" not in e.detail:
                e.detail["request_id"] = request_id
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
            )
        else:
            # Format as error response
            error_detail = {
                "error": _get_error_code_from_status(e.status_code),
                "message": str(e.detail) if e.detail else "HTTP error occurred",
                "request_id": request_id,
            }
            return JSONResponse(
                status_code=e.status_code,
                content=error_detail,
            )

    except StarletteHTTPException as e:
        # Starlette HTTP exceptions
        error_detail = {
            "error": _get_error_code_from_status(e.status_code),
            "message": str(e.detail) if e.detail else "HTTP error occurred",
            "request_id": request_id,
        }
        return JSONResponse(
            status_code=e.status_code,
            content=error_detail,
        )

    except ValueError as e:
        # 400: Bad request (invalid input)
        logger.warning(f"Value error: {e}")
        error_detail = {
            "error": "validation_error",
            "message": str(e),
            "details": {
                "issue": "invalid_value",
            },
            "request_id": request_id,
        }
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_detail,
        )

    except ConnectionError as e:
        # 503: Service unavailable (database/connection errors)
        logger.error(f"Connection error: {e}", exc_info=True)
        error_detail = {
            "error": "service_unavailable",
            "message": "Database connection failed",
            "retry_after": 30,
            "request_id": request_id,
        }
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_detail,
        )

    except RuntimeError as e:
        # Check if it's a service unavailable error
        error_msg = str(e).lower()
        if "connection" in error_msg or "unavailable" in error_msg:
            # 503: Service unavailable
            logger.error(f"Service unavailable: {e}", exc_info=True)
            error_detail = {
                "error": "service_unavailable",
                "message": "Service temporarily unavailable",
                "retry_after": 30,
                "request_id": request_id,
            }
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=error_detail,
            )
        else:
            # 500: Internal server error
            logger.error(f"Runtime error: {e}", exc_info=True)
            error_detail = {
                "error": "internal_error",
                "message": "An internal error occurred",
                "request_id": request_id,
            }
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_detail,
            )

    except Exception as e:
        # 500: Catch-all for unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        error_detail = {
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "request_id": request_id,
        }
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_detail,
        )


def _get_error_code_from_status(status_code: int) -> str:
    """
    Map HTTP status code to error code string.
    
    Args:
        status_code: HTTP status code
        
    Returns:
        Error code string
    """
    if status_code == status.HTTP_400_BAD_REQUEST:
        return "validation_error"
    elif status_code == status.HTTP_404_NOT_FOUND:
        return "no_match_found"
    elif status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        return "validation_error"
    elif status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        return "internal_error"
    elif status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        return "service_unavailable"
    else:
        return "http_error"

