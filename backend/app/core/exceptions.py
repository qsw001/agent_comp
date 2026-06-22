"""
异常处理
"""

from __future__ import annotations
from typing import Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """应用基础异常"""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[dict[str, list[str]]] = None,
    ):
        super().__init__(status_code=status_code, detail={"code": code, "message": message, "details": details})
        self.code = code
        self.message = message
        self.details = details


class NotFoundException(AppException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"{resource} '{resource_id}' not found",
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=message,
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=message,
        )


class ValidationException(AppException):
    def __init__(self, message: str, details: Optional[dict[str, list[str]]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )
