from uuid import uuid4

from .errors import AppError, ErrorCode


def success_response(data: list[dict], retries: int = 0) -> dict:
    return {
        "success": True,
        "request_id": str(uuid4()),
        "data": data,
        "error": None,
        "meta": {
            "retries": retries,
            "version": "v1",
        },
    }


def error_response(error: AppError) -> dict:
    return {
        "success": False,
        "request_id": str(uuid4()),
        "data": None,
        "error": {
            "code": error.code,
            "message": error.message,
        },
        "meta": {
            "retries": 0,
            "version": "v1",
        },
    }


def internal_error_response() -> dict:
    return error_response(AppError(ErrorCode.INTERNAL_ERROR, "Unexpected internal server error"))
