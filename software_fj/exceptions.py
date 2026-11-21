"""Custom exception hierarchy for the Software FJ system.

Every domain error inherits from SoftwareFJError, so upper layers can catch
any domain failure with a single except clause while unexpected Python
errors are still handled separately.
"""


class SoftwareFJError(Exception):
    """Base class for all domain errors."""

    code = "ERR_GENERAL"

    def __str__(self) -> str:
        # Uniform format: [CODE] message — easy to filter in the log file.
        return f"[{self.code}] {self.args[0] if self.args else ''}"


class ValidationError(SoftwareFJError):
    """Invalid data in any entity."""

    code = "ERR_VALIDATION"


class InvalidClientError(ValidationError):
    """Invalid client personal data."""

    code = "ERR_CLIENT"


class InvalidServiceError(ValidationError):
    """Invalid service parameters or unknown service type."""

    code = "ERR_SERVICE"


class MissingParameterError(ValidationError):
    """A required parameter is missing (or an unexpected one was given)."""

    code = "ERR_MISSING_PARAM"


class ServiceUnavailableError(SoftwareFJError):
    """Attempt to book a service that is not available."""

    code = "ERR_UNAVAILABLE"


class InvalidReservationError(SoftwareFJError):
    """A reservation cannot be created or processed."""

    code = "ERR_RESERVATION"


class OperationNotAllowedError(SoftwareFJError):
    """Forbidden state transition (e.g. cancelling a processed reservation)."""

    code = "ERR_OPERATION"


class InconsistentCalculationError(SoftwareFJError):
    """Cost calculation produced an invalid result."""

    code = "ERR_CALCULATION"
