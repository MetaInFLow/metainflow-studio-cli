class MetainflowError(Exception):
    """Base error for CLI domain failures."""


class ValidationError(MetainflowError):
    exit_code = 2


class ProcessingError(MetainflowError):
    exit_code = 1


class ExternalError(MetainflowError):
    exit_code = 3
