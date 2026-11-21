"""Simulation of valid and invalid operations for the Software FJ system.

Run with:  python3 main.py
Every event and error is written to logs/software_fj.log.
"""

from collections.abc import Callable

from software_fj import Reservation, SoftwareFJSystem
from software_fj.log_config import LOG_FILE, get_logger

log = get_logger("main")


def run_step(number: int, title: str, operation: Callable[[], object]) -> None:
    """Run one simulated operation; an unexpected error never stops the app."""
    print(f"\n{number:>2}. {title}")
    try:
        result = operation()
    except Exception:
        # Last safety net for bugs that are not domain errors.
        log.exception("Unexpected error in step %d (%s)", number, title)
        print("    -> UNEXPECTED ERROR (see log); the system keeps running")
    else:
        ok = result not in (None, False)
        print(f"    -> {'OK' if ok else 'REJECTED (see log)'}: {result if ok else ''}")


def main() -> None:
    system = SoftwareFJSystem()
    # Reservations created during the simulation, referenced by later steps
    # (avoids hard-coding generated IDs).
    booked: dict[str, Reservation | None] = {}

    def book(key: str, document: str, service: str, duration: float) -> Reservation | None:
        booked[key] = system.create_reservation(document, service, duration)
        return booked[key]

    def rid(key: str) -> str:
        reservation = booked.get(key)
        return reservation.id if reservation else "<not created>"

    # (title, operation) pairs: valid and invalid cases mixed on purpose.
    steps: list[tuple[str, Callable[[], object]]] = [
        # --- Clients ---
        ("Register valid client Ana Gomez",
         lambda: system.register_client("Ana Gomez", "1023456789", "ana.gomez@mail.com", "3001234567")),
        ("Register valid client Luis Perez",
         lambda: system.register_client("Luis Perez", "79865432", "luis@empresa.co", "3109876543")),
        ("Register client with invalid email (should fail)",
         lambda: system.register_client("Carlos Ruiz", "52123456", "carlos-at-mail", "3201112233")),
        ("Register client with duplicated document (should fail)",
         lambda: system.register_client("Ana Maria", "1023456789", "ana2@mail.com", "3001112233")),
        ("Register client with missing name (should fail)",
         lambda: system.register_client("", "11223344", "x@mail.com", "3001234567")),
        # --- Services ---
        ("Create room 'Sala Andes' for 30 people",
         lambda: system.create_service("room", name="Sala Andes", base_rate=80_000, capacity=30)),
        ("Create equipment rental 'Projector'",
         lambda: system.create_service("equipment", name="Projector", base_rate=40_000, quantity=2)),
        ("Create expert consulting 'Cloud Architecture'",
         lambda: system.create_service("consulting", name="Cloud Architecture", base_rate=150_000,
                                       specialty="AWS", level="expert")),
        ("Create service with negative rate (should fail)",
         lambda: system.create_service("room", name="Sala Caribe", base_rate=-1000, capacity=10)),
        ("Create service of unknown type (should fail)",
         lambda: system.create_service("catering", name="Lunch", base_rate=20_000)),
        ("Create consulting missing 'level' parameter (should fail, chained TypeError)",
         lambda: system.create_service("consulting", name="Data Science", base_rate=120_000, specialty="ML")),
        # --- Reservations ---
        ("Book 'Sala Andes' 4 hours for Ana",
         lambda: book("room", "1023456789", "Sala Andes", 4)),
        ("Confirm and process with VAT + 10% discount",
         lambda: system.confirm_reservation(rid("room"))
         and system.process_reservation(rid("room"), tax=0.19, discount=0.10)),
        ("Book 'Projector' for 2.5 days (should fail: whole days only, chained error)",
         lambda: book("bad_days", "79865432", "Projector", 2.5)),
        ("Book for an unregistered client (should fail)",
         lambda: book("ghost", "99999999", "Projector", 3)),
        ("Book 'Cloud Architecture' 3 hours for Luis",
         lambda: book("consulting", "79865432", "Cloud Architecture", 3)),
        ("Consultant becomes unavailable, then confirm (should fail)",
         lambda: system.find_service("Cloud Architecture").set_available(False)
         or system.confirm_reservation(rid("consulting"))),
        ("Process a reservation that is still pending (should fail)",
         lambda: system.process_reservation(rid("consulting"))),
        ("Cancel the pending consulting reservation",
         lambda: system.cancel_reservation(rid("consulting"))),
        ("Cancel an already processed reservation (should fail)",
         lambda: system.cancel_reservation(rid("room"))),
        ("Book 'Projector' 5 days, confirm and process with invalid tax 150% (should fail)",
         lambda: book("projector", "79865432", "Projector", 5)
         and system.confirm_reservation(rid("projector"))
         and system.process_reservation(rid("projector"), tax=1.5)),
        ("Retry the same reservation with standard 19% VAT (succeeds)",
         lambda: system.process_reservation(rid("projector"), tax=0.19)),
    ]

    print("=" * 70)
    print(" SOFTWARE FJ - Client, service and reservation management simulation")
    print("=" * 70)

    for number, (title, operation) in enumerate(steps, start=1):
        run_step(number, title, operation)

    print("\n" + "=" * 70)
    print(" FINAL STATE")
    print("=" * 70)
    for reservation in system.reservations:
        print(f"  {reservation}")
    print(f"\n  {system.summary()}")
    print(f"\n  Log file: {LOG_FILE}")
    log.info("Simulation finished. %s", system.summary())


if __name__ == "__main__":
    main()
