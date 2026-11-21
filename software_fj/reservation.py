"""Reservation entity: ties together client, service, duration and status."""

from enum import Enum

from .client import Client
from .entity import Entity
from .exceptions import (
    InconsistentCalculationError,
    InvalidReservationError,
    InvalidServiceError,
    OperationNotAllowedError,
    ServiceUnavailableError,
)
from .log_config import get_logger
from .services import Service

log = get_logger("reservation")


class ReservationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    PROCESSED = "processed"


class Reservation(Entity):
    """Lifecycle: PENDING -> CONFIRMED -> PROCESSED, or -> CANCELLED."""

    def __init__(self, client: Client, service: Service, duration: float):
        # Validate BEFORE calling super(): rejected reservations must not
        # consume an identifier from the sequence.
        if not isinstance(client, Client):
            raise InvalidReservationError("A reservation requires a valid Client.")
        if not isinstance(service, Service):
            raise InvalidReservationError("A reservation requires a valid Service.")

        try:
            # Each service validates duration its own way (polymorphism).
            service.validate_duration(duration)
        except InvalidServiceError as error:
            # Exception chaining: translate to a reservation error while
            # keeping the original cause in __cause__.
            raise InvalidReservationError(f"Invalid duration for '{service.name}'.") from error

        super().__init__()
        self.__client = client
        self.__service = service
        self.__duration = duration
        self.__status = ReservationStatus.PENDING
        self.__total_cost: float | None = None

    @property
    def client(self) -> Client:
        return self.__client

    @property
    def service(self) -> Service:
        return self.__service

    @property
    def duration(self) -> float:
        return self.__duration

    @property
    def status(self) -> ReservationStatus:
        return self.__status

    @property
    def total_cost(self) -> float | None:
        return self.__total_cost

    # ---------- Lifecycle operations ----------

    def confirm(self) -> None:
        """PENDING -> CONFIRMED, only if the service is available."""
        if self.__status is not ReservationStatus.PENDING:
            raise OperationNotAllowedError(f"Cannot confirm a {self.__status.value} reservation.")
        if not self.__service.available:
            raise ServiceUnavailableError(f"Service '{self.__service.name}' is not available.")
        self.__status = ReservationStatus.CONFIRMED
        log.info("Reservation %s confirmed.", self.id)

    def cancel(self) -> None:
        """Cancel unless already processed or cancelled."""
        if self.__status in (ReservationStatus.PROCESSED, ReservationStatus.CANCELLED):
            raise OperationNotAllowedError(f"Cannot cancel a {self.__status.value} reservation.")
        self.__status = ReservationStatus.CANCELLED
        log.info("Reservation %s cancelled.", self.id)

    def process(self, tax: float = 0.0, discount: float = 0.0) -> float:
        """CONFIRMED -> PROCESSED, computing the final cost.

        try/except/else/finally:
          - try:     compute the cost.
          - except:  translate the calculation error (chaining).
          - else:    runs only on success; updates the state.
          - finally: ALWAYS records the attempt in the log.
        """
        if self.__status is not ReservationStatus.CONFIRMED:
            raise OperationNotAllowedError(
                f"Only confirmed reservations can be processed (current: {self.__status.value})."
            )

        succeeded = False
        try:
            cost = self.__service.calculate_cost(self.__duration, tax, discount)
        except InconsistentCalculationError as error:
            raise InvalidReservationError(f"Reservation {self.id} could not be processed.") from error
        else:
            self.__total_cost = cost
            self.__status = ReservationStatus.PROCESSED
            succeeded = True
            return cost
        finally:
            log.info("Processing attempt for %s -> %s", self.id, "OK" if succeeded else "FAILED")

    def validate(self) -> None:
        self.__client.validate()
        self.__service.validate_duration(self.__duration)

    def describe(self) -> str:
        cost = f" | total ${self.__total_cost:,.2f}" if self.__total_cost is not None else ""
        return (
            f"Reservation {self.id}: {self.__client.name} -> {self.__service.name} "
            f"({self.__duration} {self.__service.unit}) [{self.__status.value}]{cost}"
        )
