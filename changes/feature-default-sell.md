# changes/feature-default-sell.md

Scope
- Make the CLI default behavior align with conventional limit rules:
  - `buy` rules trigger when price <= target (BELOW)
  - `sell` rules trigger when price >= target (ABOVE)

What was added/changed
- `trader/cli/main.py`: Default rule condition logic updated so `sell` defaults to `ABOVE` when `--above` is not provided; `--above` still overrides.
- `README.md`: Examples updated to reflect new defaults for `sell` rules.
- `tests/test_rules.py`: No functional changes required since tests already covered `ABOVE` and `BELOW` behavior; full test suite run and passed.

Files changed
- trader/cli/main.py
- README.md
- CHANGELOG.md

Tests added/changed
- Ran existing test suite; all tests passed (60 passed).
- No new tests were necessary; consider adding a CLI-level test asserting `trader rules add sell` produces `RuleCondition.ABOVE`.

Status
- done

Notes
- If you want `--above` removed as a flag (no-op) we can remove it, but keeping it preserves explicitness.
- Consider a follow-up: add a unit test that calls the CLI entrypoint to verify the default mapping for `buy`/`sell`.
