.PHONY: test lint coverage dist

test:
	pytest

lint:
	flake8 . --count --show-source --statistics

coverage:
	coverage run -m pytest
	coverage html

dist:
	python -m build
