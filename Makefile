.PHONY: test lint

lint:
	ruff check src tests
	test -d results || mkdir -p results
	test -d docs || mkdir -p docs

test:
	pytest
