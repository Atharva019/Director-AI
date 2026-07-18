# Manual scripts

Not part of the test suite — these hit live external services.

- `check_nim.py` — sends a tiny image to the configured NVIDIA NIM endpoint and
  prints the raw response. Use it to confirm an API key works.

  ```bash
  cd backend && PYTHONPATH=. venv/bin/python scripts/check_nim.py
  ```
