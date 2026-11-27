# Changelog

## [1.0.0] - 2026-11-27

### Added
- Pluggable multi-sector corporate job portal adapters (Tech, Defense, Banking, Aviation, Enterprise).
- Deduplicated SQLite persistence (`JobStorage`), Rich CLI (`main.py`), and FastAPI web dashboard.
- Offline deterministic storage & deduplication edge-case suite (`tests/test_edge_cases.py`).
- GitHub Actions CI (Python 3.11/3.12 + Docker build) and Dependabot configuration.
