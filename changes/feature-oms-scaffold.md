# changes/feature-oms-scaffold.md

Scope
- Implement initial Order Management System (OMS) scaffolding.
- Provide order model, lifecycle constants, and basic validation tests.

What will be added
- `trader/models/order.py` (order model dataclass)
- `tests/test_orders.py` with basic lifecycle and validation tests
- `CHANGELOG.md` entry (unreleased) updated when implementation completes

Status
- in-progress

Notes
- This is an incremental change: start with tests and minimal model, then expand to validators and persistence in later steps.
