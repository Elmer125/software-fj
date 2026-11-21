"""System facade: manages in-memory lists of clients, services and reservations.

Every public method catches domain errors, logs them and returns None/False
instead of stopping the application.
"""

from .client import Client
from .exceptions import (
    InvalidClientError,
    InvalidReservationError,
    InvalidServiceError,
    MissingParameterError,
    SoftwareFJError,
)
from .log_config import get_logger
from .reservation import Reservation
from .services import Consulting, EquipmentRental, RoomBooking, Service

log = get_logger("system")


def _with_cause(error: BaseException) -> str:
    """Render an error plus its chained cause, if any."""
    return f"{error} | caused by: {error.__cause__!r}" if error.__cause__ else str(error)


class SoftwareFJSystem:
    """In-memory (no database) management for Software FJ."""

    # Factory registry: adding a new service type only requires one entry here.
    SERVICE_TYPES: dict[str, type[Service]] = {
        "room": RoomBooking,
        "equipment": EquipmentRental,
        "consulting": Consulting,
    }

    def __init__(self):
        # Internal lists: the only "storage" of the system.
        self._clients: list[Client] = []
        self._services: list[Service] = []
        self._reservations: list[Reservation] = []
        log.info("=== Software FJ system started ===")

    # ---------- Queries (read-only views) ----------

    @property
    def clients(self) -> tuple[Client, ...]:
        return tuple(self._clients)

    @property
    def services(self) -> tuple[Service, ...]:
        return tuple(self._services)

    @property
    def reservations(self) -> tuple[Reservation, ...]:
        return tuple(self._reservations)

    def find_client(self, document: str) -> Client:
        for client in self._clients:
            if client.document == str(document):
                return client
        raise InvalidClientError(f"No client with document {document}.")

    def find_service(self, name: str) -> Service:
        for service in self._services:
            if service.name.lower() == str(name).lower():
                return service
        raise InvalidServiceError(f"Service '{name}' does not exist.")

    def find_reservation(self, reservation_id: str) -> Reservation:
        for reservation in self._reservations:
            if reservation.id == reservation_id:
                return reservation
        raise InvalidReservationError(f"Reservation {reservation_id} does not exist.")

    # ---------- Commands ----------

    def register_client(self, name, document, email, phone) -> Client | None:
        try:
            client = Client(name, document, email, phone)
            if any(c.document == client.document for c in self._clients):
                raise InvalidClientError(f"Document {client.document} is already registered.")
        except SoftwareFJError as error:
            log.error("Client registration rejected: %s", error)
            return None
        else:
            # Runs only if no exception was raised.
            self._clients.append(client)
            log.info("Client registered: %s", client)
            return client

    def create_service(self, service_type: str, **params) -> Service | None:
        try:
            service_class = self.SERVICE_TYPES.get(service_type)
            if service_class is None:
                raise InvalidServiceError(f"Unknown service type: '{service_type}'.")
            try:
                service = service_class(**params)
            except TypeError as error:
                # Chaining: a Python TypeError (missing/unexpected argument)
                # becomes a domain error that keeps the original cause.
                raise MissingParameterError(f"Wrong parameters for '{service_type}'.") from error
            if any(s.name.lower() == service.name.lower() for s in self._services):
                raise InvalidServiceError(f"A service named '{service.name}' already exists.")
        except SoftwareFJError as error:
            log.error("Service creation rejected: %s", _with_cause(error))
            return None
        else:
            self._services.append(service)
            log.info("Service created: %s", service)
            return service

    def create_reservation(self, document: str, service_name: str, duration: float) -> Reservation | None:
        try:
            reservation = Reservation(self.find_client(document), self.find_service(service_name), duration)
        except SoftwareFJError as error:
            log.error("Reservation rejected: %s", _with_cause(error))
            return None
        else:
            self._reservations.append(reservation)
            log.info("Reservation created: %s", reservation)
            return reservation

    def confirm_reservation(self, reservation_id: str) -> bool:
        try:
            self.find_reservation(reservation_id).confirm()
            return True
        except SoftwareFJError as error:
            log.error("Confirmation failed for %s: %s", reservation_id, error)
            return False

    def cancel_reservation(self, reservation_id: str) -> bool:
        try:
            self.find_reservation(reservation_id).cancel()
            return True
        except SoftwareFJError as error:
            log.error("Cancellation failed for %s: %s", reservation_id, error)
            return False

    def process_reservation(self, reservation_id: str, tax: float = 0.0, discount: float = 0.0) -> float | None:
        try:
            return self.find_reservation(reservation_id).process(tax, discount)
        except SoftwareFJError as error:
            log.error("Processing failed for %s: %s", reservation_id, _with_cause(error))
            return None

    def summary(self) -> str:
        processed = [r for r in self._reservations if r.total_cost is not None]
        revenue = sum(r.total_cost for r in processed)
        return (
            f"Clients: {len(self._clients)} | Services: {len(self._services)} | "
            f"Reservations: {len(self._reservations)} (processed: {len(processed)}) | "
            f"Revenue: ${revenue:,.2f}"
        )
