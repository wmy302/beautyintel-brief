PY ?= C:/Users/64554/AppData/Local/Programs/Python/Python313/python.exe

.PHONY: install init-db ingest-demo brief-demo run-api test

install:
	$(PY) -m pip install -r requirements.txt

init-db:
	$(PY) -m app.cli init-db

ingest-demo:
	$(PY) -m app.cli ingest --dry-run

brief-demo:
	$(PY) -m app.cli ingest && $(PY) -m app.cli generate-report --today

run-api:
	$(PY) -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	$(PY) -m pytest
