"""Abstract Service and its three specialized services.

Polymorphism: each subclass overrides base_cost(), validate_duration() and
describe(). Reservation works with any Service without knowing its type.
"""

from abc import abstractmethod
from typing import overload

from .entity import Entity
from .exceptions import InconsistentCalculationError, InvalidServiceError

COLOMBIA_VAT = 0.19


def _is_number(value) -> bool:
    # bool is a subclass of int, so it is excluded explicitly.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class Service(Entity):
    """Generic service offered by Software FJ."""

    def __init__(self, name: str, base_rate: float, available: bool = True):
        super().__init__()
        if not isinstance(name, str) or len(name.strip()) < 3:
            raise InvalidServiceError(f"Invalid service name: {name!r}")
        if not _is_number(base_rate) or base_rate <= 0:
            raise InvalidServiceError(f"Base rate must be a positive number: {base_rate!r}")
        self.__name = name.strip()
        self.__base_rate = float(base_rate)
        self.__available = bool(available)

    @property
    def name(self) -> str:
        return self.__name

    @property
    def base_rate(self) -> float:
        return self.__base_rate

    @property
    def available(self) -> bool:
        return self.__available

    def set_available(self, available: bool) -> None:
        """Toggle availability (e.g. room under maintenance)."""
        self.__available = bool(available)

    # ---------- Contract for specialized services ----------

    @property
    @abstractmethod
    def unit(self) -> str:
        """Duration unit: 'hours' or 'days'."""

    @abstractmethod
    def validate_duration(self, duration: float) -> None:
        """Validate the duration according to the service rules."""

    @abstractmethod
    def base_cost(self, duration: float) -> float:
        """Cost before taxes and discounts."""

    def validate(self) -> None:
        if self.base_rate <= 0:
            raise InvalidServiceError("Inconsistent base rate.")

    # ---------- "Overloaded" cost calculation ----------
    # Python has no real method overloading (a second def replaces the first).
    # It is emulated with optional parameters; @overload documents the
    # supported signatures for type checkers and readers:
    #   calculate_cost(d)                  -> base cost
    #   calculate_cost(d, tax)             -> cost with tax
    #   calculate_cost(d, tax, discount)   -> cost with tax and discount

    @overload
    def calculate_cost(self, duration: float) -> float: ...
    @overload
    def calculate_cost(self, duration: float, tax: float) -> float: ...
    @overload
    def calculate_cost(self, duration: float, tax: float, discount: float) -> float: ...

    def calculate_cost(self, duration, tax=0.0, discount=0.0):
        """Final cost = base × (1 − discount) × (1 + tax). Rates go from 0 to 1."""
        self.validate_duration(duration)
        if not _is_number(tax) or not 0 <= tax <= 1:
            raise InconsistentCalculationError(f"Tax out of range: {tax!r}")
        if not _is_number(discount) or not 0 <= discount < 1:
            raise InconsistentCalculationError(f"Discount out of range: {discount!r}")

        total = self.base_cost(duration) * (1 - discount) * (1 + tax)

        # Defensive check: a cost can never be zero or negative.
        if total <= 0:
            raise InconsistentCalculationError(f"Invalid computed cost: {total}")
        return round(total, 2)

    def calculate_cost_with_vat(self, duration: float, discount: float = 0.0) -> float:
        """Shortcut for the most common variant: Colombian 19% VAT."""
        return self.calculate_cost(duration, COLOMBIA_VAT, discount)


class RoomBooking(Service):
    """Room booking, billed per hour (1 to 12)."""

    LARGE_ROOM_SURCHARGE = 0.10

    def __init__(self, name: str, base_rate: float, capacity: int, available: bool = True):
        super().__init__(name, base_rate, available)
        if not isinstance(capacity, int) or not 1 <= capacity <= 200:
            raise InvalidServiceError(f"Invalid room capacity: {capacity!r}")
        self.capacity = capacity

    @property
    def unit(self) -> str:
        return "hours"

    def validate_duration(self, duration: float) -> None:
        if not _is_number(duration) or not 1 <= duration <= 12:
            raise InvalidServiceError(f"Rooms are booked for 1 to 12 hours (got {duration!r}).")

    def base_cost(self, duration: float) -> float:
        cost = self.base_rate * duration
        # Rooms for more than 20 people carry a 10% surcharge.
        if self.capacity > 20:
            cost *= 1 + self.LARGE_ROOM_SURCHARGE
        return cost

    def describe(self) -> str:
        return f"Room '{self.name}' for {self.capacity} people - ${self.base_rate:,.0f}/hour"


class EquipmentRental(Service):
    """Equipment rental, billed per whole day (1 to 30) plus daily insurance."""

    DAILY_INSURANCE = 5_000

    def __init__(self, name: str, base_rate: float, quantity: int, available: bool = True):
        super().__init__(name, base_rate, available)
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            raise InvalidServiceError(f"Invalid equipment quantity: {quantity!r}")
        self.quantity = quantity

    @property
    def unit(self) -> str:
        return "days"

    def validate_duration(self, duration: float) -> None:
        if not isinstance(duration, int) or isinstance(duration, bool) or not 1 <= duration <= 30:
            raise InvalidServiceError(f"Equipment is rented for 1 to 30 whole days (got {duration!r}).")

    def base_cost(self, duration: float) -> float:
        return (self.base_rate * self.quantity + self.DAILY_INSURANCE) * duration

    def describe(self) -> str:
        return f"Rental of {self.quantity} x '{self.name}' - ${self.base_rate:,.0f}/day each"


class Consulting(Service):
    """Specialized consulting, billed per hour (1 to 8) by consultant level."""

    LEVEL_MULTIPLIERS = {"junior": 1.0, "senior": 1.5, "expert": 2.0}

    def __init__(self, name: str, base_rate: float, specialty: str, level: str, available: bool = True):
        super().__init__(name, base_rate, available)
        if not isinstance(specialty, str) or not specialty.strip():
            raise InvalidServiceError("Consulting requires a specialty.")
        if level not in self.LEVEL_MULTIPLIERS:
            raise InvalidServiceError(f"Unknown level '{level}'. Options: {list(self.LEVEL_MULTIPLIERS)}")
        self.specialty = specialty.strip()
        self.level = level

    @property
    def unit(self) -> str:
        return "hours"

    def validate_duration(self, duration: float) -> None:
        if not _is_number(duration) or not 1 <= duration <= 8:
            raise InvalidServiceError(f"Consulting lasts 1 to 8 hours (got {duration!r}).")

    def base_cost(self, duration: float) -> float:
        return self.base_rate * duration * self.LEVEL_MULTIPLIERS[self.level]

    def describe(self) -> str:
        return f"Consulting '{self.name}' on {self.specialty} ({self.level} level)"
