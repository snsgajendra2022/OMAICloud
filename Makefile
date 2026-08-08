.PHONY: install test api smoke
install:
	python3 -m pip install -e '.[dev]'

test:
	pytest -q

api:
	om-ai serve --host 0.0.0.0 --port 8080

smoke:
	python3 scripts/smoke_test.py
