# lab-ci

Лабораторна робота №4: unit-тести (pytest) та CI/CD з GitHub Actions.

## Локальний запуск

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

ruff check .
ruff format --check .
mypy src tests
pytest -v
```
