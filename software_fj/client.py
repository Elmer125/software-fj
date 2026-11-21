"""Client entity with strict validation and encapsulated personal data."""

import re

from .entity import Entity
from .exceptions import InvalidClientError

_EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
_NAME_PATTERN = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{3,60}$")


class Client(Entity):
    """A Software FJ client.

    Personal data lives in private attributes and can only change through
    validating setters, so an invalid Client can never exist.
    """

    def __init__(self, name: str, document: str, email: str, phone: str):
        # The national ID document is the client's natural identifier.
        super().__init__(identifier=str(document) if document else None)
        # Assign through setters so validation also runs on creation.
        self.name = name
        self.document = document
        self.email = email
        self.phone = phone

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str) or not _NAME_PATTERN.match(value.strip()):
            raise InvalidClientError(f"Invalid name: {value!r}")
        self.__name = value.strip().title()

    @property
    def document(self) -> str:
        return self.__document

    @document.setter
    def document(self, value: str) -> None:
        value = str(value).strip() if value is not None else ""
        if not value.isdigit() or not 6 <= len(value) <= 10:
            raise InvalidClientError(f"Invalid document: {value!r} (6 to 10 digits)")
        self.__document = value

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, value: str) -> None:
        if not isinstance(value, str) or not _EMAIL_PATTERN.match(value.strip()):
            raise InvalidClientError(f"Invalid email: {value!r}")
        self.__email = value.strip().lower()

    @property
    def phone(self) -> str:
        return self.__phone

    @phone.setter
    def phone(self, value: str) -> None:
        value = str(value).strip() if value is not None else ""
        if not value.isdigit() or not 7 <= len(value) <= 10:
            raise InvalidClientError(f"Invalid phone: {value!r} (7 to 10 digits)")
        self.__phone = value

    def validate(self) -> None:
        # Re-assigning forces every value through its setter again.
        self.name, self.document = self.name, self.document
        self.email, self.phone = self.email, self.phone

    def describe(self) -> str:
        # Email is masked so personal data does not leak into logs.
        user, domain = self.email.split("@")
        return f"Client {self.name} (doc {self.document}, {user[0]}***@{domain})"
