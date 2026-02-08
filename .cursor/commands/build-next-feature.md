## build-next-feature

Autonomously pick the next feature from `PLAN.md` (based on current phase/status) and complete it end‑to‑end:
- Review `PLAN.md`, select the highest‑priority unfinished item, and keep `PLAN.md` updated as you work.
- Create a new branch with a clear name.
- Implement the feature fully (prefer modular abstractions, no silent failures).
- Preserve backward compatibility for CLI/data paths; add shims if needed.
- Add or update tests; run tests, fix failures, and re‑run until green (report warnings).
- Update docs: `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md` as needed.
- Update config/env docs if new settings are introduced.
- Ensure data/cache artifacts are not committed.
- Commit with a concise, meaningful message; push the branch.
- Open a PR
