"""Abstract base class for every general entity in the system."""

from abc import ABC, abstractmethod
from itertools import count

from .exceptions import MissingParameterError


class Entity(ABC):
    """Common contract for Client, Service and Reservation.

    Every entity has an identifier, can describe itself and can validate itself.
    """

    # One independent sequence per concrete class (RES-0001, SER-0001, ...).
    _sequences: dict[type, count] = {}

    def __init__(self, identifier: str | None = None):
        if identifier is None:
            sequence = Entity._sequences.setdefault(type(self), count(1))
            identifier = f"{type(self).__name__[:3].upper()}-{next(sequence):04d}"
        if not isinstance(identifier, str) or not identifier.strip():
            raise MissingParameterError("An entity requires a non-empty identifier.")
        # Name-mangled private attribute: read-only through the property.
        self.__id = identifier.strip()

    @property
    def id(self) -> str:
        return self.__id

    @abstractmethod
    def describe(self) -> str:
        """Human-readable description (polymorphic)."""

    @abstractmethod
    def validate(self) -> None:
        """Raise an exception if the entity state is invalid."""

    def __str__(self) -> str:
        return self.describe()
