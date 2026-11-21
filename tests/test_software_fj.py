"""Unit tests. Run with:  python3 -m unittest discover -s tests -v"""

import unittest

from software_fj import Client, Consulting, EquipmentRental, Reservation, ReservationStatus, RoomBooking
from software_fj.exceptions import (
    InconsistentCalculationError,
    InvalidClientError,
    InvalidReservationError,
    InvalidServiceError,
    OperationNotAllowedError,
    ServiceUnavailableError,
)
from software_fj.system import SoftwareFJSystem


def make_client() -> Client:
    return Client("Ana Gomez", "1023456789", "ana@mail.com", "3001234567")


class ClientTests(unittest.TestCase):
    def test_valid_client_is_created(self):
        self.assertEqual(make_client().name, "Ana Gomez")

    def test_invalid_email_raises(self):
        with self.assertRaises(InvalidClientError):
            Client("Ana Gomez", "1023456789", "not-an-email", "3001234567")

    def test_setter_validates_after_creation(self):
        client = make_client()
        with self.assertRaises(InvalidClientError):
            client.phone = "12"


class ServiceTests(unittest.TestCase):
    def test_polymorphic_costs(self):
        room = RoomBooking("Sala", 100, capacity=30)            # +10% surcharge
        rental = EquipmentRental("Laptop", 100, quantity=2)     # + daily insurance
        consulting = Consulting("Cloud", 100, "AWS", "senior")  # x1.5
        self.assertEqual(room.calculate_cost(2), 220.0)
        self.assertEqual(rental.calculate_cost(1), 5200.0)
        self.assertEqual(consulting.calculate_cost(2), 300.0)

    def test_overloaded_variants(self):
        room = RoomBooking("Sala", 100, capacity=10)
        self.assertEqual(room.calculate_cost(1), 100.0)
        self.assertEqual(room.calculate_cost(1, 0.19), 119.0)
        self.assertEqual(room.calculate_cost(1, 0.19, 0.5), 59.5)
        self.assertEqual(room.calculate_cost_with_vat(1), 119.0)

    def test_invalid_rate_raises(self):
        with self.assertRaises(InvalidServiceError):
            RoomBooking("Sala", -5, capacity=10)

    def test_inconsistent_tax_raises(self):
        with self.assertRaises(InconsistentCalculationError):
            RoomBooking("Sala", 100, capacity=10).calculate_cost(1, tax=2)


class ReservationTests(unittest.TestCase):
    def setUp(self):
        self.service = RoomBooking("Sala", 100, capacity=10)
        self.reservation = Reservation(make_client(), self.service, 2)

    def test_invalid_duration_is_chained(self):
        with self.assertRaises(InvalidReservationError) as ctx:
            Reservation(make_client(), self.service, 50)
        self.assertIsInstance(ctx.exception.__cause__, InvalidServiceError)

    def test_full_lifecycle(self):
        self.reservation.confirm()
        self.assertEqual(self.reservation.process(0.19), 238.0)
        self.assertIs(self.reservation.status, ReservationStatus.PROCESSED)

    def test_unavailable_service_cannot_be_confirmed(self):
        self.service.set_available(False)
        with self.assertRaises(ServiceUnavailableError):
            self.reservation.confirm()

    def test_processed_reservation_cannot_be_cancelled(self):
        self.reservation.confirm()
        self.reservation.process()
        with self.assertRaises(OperationNotAllowedError):
            self.reservation.cancel()

    def test_failed_processing_keeps_state(self):
        self.reservation.confirm()
        with self.assertRaises(InvalidReservationError):
            self.reservation.process(tax=5)
        self.assertIs(self.reservation.status, ReservationStatus.CONFIRMED)


class SystemTests(unittest.TestCase):
    def test_errors_never_propagate(self):
        system = SoftwareFJSystem()
        self.assertIsNone(system.register_client("", "", "", ""))
        self.assertIsNone(system.create_service("unknown"))
        self.assertIsNone(system.create_service("consulting", name="X ray", base_rate=1))
        self.assertIsNone(system.create_reservation("1", "nothing", 1))
        self.assertFalse(system.confirm_reservation("RES-9999"))


if __name__ == "__main__":
    unittest.main()
