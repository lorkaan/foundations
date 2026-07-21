class BackendException(Exception):
    """Base exception for backend failures."""
    pass


class BackendNotFound(BackendException):
    """Raised when a requested backend is not registered."""
    pass


class InvalidBackend(BackendException):
    """Raised when a backend does not implement the required interface."""
    pass


class BackendConfigurationError(BackendException):
    """Raised when backend configuration is invalid."""
    pass