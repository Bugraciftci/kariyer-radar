# Contributing

1. Fork the repository and install dependencies with `pip install -r requirements.txt`.
2. Run deterministic tests locally with `python -m unittest tests.test_radar.TestJobModelAndStorage tests.test_edge_cases -v`.
3. Keep portal adapters isolated under `radar/adapters/` with clear timeouts and error handling.
