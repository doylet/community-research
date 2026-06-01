from dataclasses import dataclass

import prawcore


class ErrorCode:
    INVALID_INPUT = "INVALID_INPUT"
    AUTH_CONFIGURATION_ERROR = "AUTH_CONFIGURATION_ERROR"
    UPSTREAM_RATE_LIMIT = "UPSTREAM_RATE_LIMIT"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class AppError(Exception):
    code: str
    message: str
    retryable: bool = False

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def map_reddit_exception(exc: Exception) -> AppError:
    if isinstance(exc, AppError):
        return exc

    if isinstance(exc, prawcore.exceptions.TooManyRequests):
        return AppError(ErrorCode.UPSTREAM_RATE_LIMIT, "Reddit API rate limit exceeded")

    if isinstance(exc, (prawcore.exceptions.RequestException, prawcore.exceptions.ResponseException, prawcore.exceptions.ServerError)):
        return AppError(ErrorCode.UPSTREAM_UNAVAILABLE, "Reddit API is temporarily unavailable", retryable=True)

    if isinstance(exc, (prawcore.exceptions.Forbidden, prawcore.exceptions.OAuthException)):
        return AppError(ErrorCode.AUTH_CONFIGURATION_ERROR, "Reddit credentials are invalid or unauthorized")

    return AppError(ErrorCode.INTERNAL_ERROR, "Unexpected internal server error")
