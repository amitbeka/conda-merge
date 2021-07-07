test:
	pytest
lint:
	pycodestyle --max-line-length=100 *.py
build:
	rm -rf build dist
	python setup.py sdist
upload:
	twine upload -u amitbeka dist/*
upload-test:
	twine upload -u amitbeka -r testpypi dist/*

.PHONY: test lint build upload upload-test
