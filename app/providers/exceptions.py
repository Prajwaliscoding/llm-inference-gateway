class ProviderError(Exception):
    """Base for all provider-side failures."""

class ProviderTimeoutError(ProviderError):
    pass

class ProviderConnectionError(ProviderError):
    pass

class ProviderServerError(ProviderError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(message)