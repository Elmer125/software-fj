# Software FJ — Client, Service & Reservation Management

Object-oriented system (no database) that manages clients, services and reservations for the fictional company **Software FJ**, with robust exception handling and event/error logging.

Course: Programación (213023) — UNAD, Phase 4.

## Run

```bash
python3 main.py                              # simulation: 22 valid/invalid operations
python3 -m unittest discover -s tests -v     # unit tests
```

Requires Python 3.10+. No external dependencies. Events and errors are written to `logs/software_fj.log`.

## Structure

```
software_fj/
├── exceptions.py   # Custom exception hierarchy (SoftwareFJError → ...)
├── log_config.py   # Log file setup (the only file the system writes)
├── entity.py       # Entity: abstract base for every domain object
├── client.py       # Client: encapsulated, validated personal data
├── services.py     # Service (abstract) + RoomBooking, EquipmentRental, Consulting
├── reservation.py  # Reservation: confirm / cancel / process lifecycle
└── system.py       # SoftwareFJSystem: in-memory lists + error-safe facade
main.py             # Simulation script
tests/              # unittest suite
```

## How each requirement is covered

| Requirement | Where |
|---|---|
| Abstract class for general entities | `Entity` (`entity.py`) |
| Client with validation + encapsulation | `Client` — private attributes, validating setters |
| Abstract Service + 3 specializations | `Service` → `RoomBooking`, `EquipmentRental`, `Consulting` |
| Polymorphism / overridden methods | `base_cost()`, `validate_duration()`, `describe()` |
| Reservation (client, service, duration, status) | `Reservation` + `ReservationStatus` enum |
| Overloaded methods | `Service.calculate_cost(d[, tax[, discount]])` with `@overload`, plus `calculate_cost_with_vat()` |
| Custom exceptions | `exceptions.py` (9 classes) |
| `try/except` | every `SoftwareFJSystem` command |
| `try/except/else` | `register_client`, `create_service`, `create_reservation` |
| `try/except/finally` | `configure_logger`, `Reservation.process` (`try/except/else/finally`) |
| Exception chaining (`raise ... from`) | `Reservation.__init__`, `Reservation.process`, `create_service` |
| Log file | `logs/software_fj.log` |
| ≥ 10 simulated operations | `main.py` (22 operations) |
| App never stops | domain errors caught in `system.py`; last-resort `except Exception` in `main.run_step` |

> **Note on overloading:** Python has no real method overloading — a second `def` with the same name replaces the first. It is emulated with optional parameters, and `typing.overload` documents the supported signatures.

## Lifecycle

```
PENDING ──confirm()──▶ CONFIRMED ──process()──▶ PROCESSED
   │                       │
   └──────cancel()─────────┴──▶ CANCELLED
```
