.PHONY: test lint coverage dist pypi testpypi

test:
	pytest

lint:
	flake8 . --count --show-source --statistics

coverage:
	coverage run -m pytest
	coverage html

dist:
	python -m build

pypi: dist
	python -m twine upload dist/*

testpypi: dist
	python -m twine upload --repository testpypi dist/*
