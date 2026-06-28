class BaseDomainException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        http_status: int,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details or {}


class DomainValidationException(BaseDomainException):
    def __init__(self, code: str, message: str, details: dict | None = None) -> None:
        super().__init__(code=code, message=message, http_status=422, details=details)


class DomainForbiddenException(BaseDomainException):
    def __init__(self, code: str, message: str, details: dict | None = None) -> None:
        super().__init__(code=code, message=message, http_status=403, details=details)


class DomainNotFoundException(BaseDomainException):
    def __init__(self, code: str, message: str, details: dict | None = None) -> None:
        super().__init__(code=code, message=message, http_status=404, details=details)


class DomainConflictException(BaseDomainException):
    def __init__(self, code: str, message: str, details: dict | None = None) -> None:
        super().__init__(code=code, message=message, http_status=409, details=details)


class DomainUnauthorizedException(BaseDomainException):
    def __init__(self, code: str, message: str, details: dict | None = None) -> None:
        super().__init__(code=code, message=message, http_status=401, details=details)
