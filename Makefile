test:
	pytest
lint:
	pycodestyle --max-line-length=100 *.py
build:
	rm -rf build dist
	python setup.py bdist
upload:
	twine upload -u amitbeka dist/*

.PHONY: test lint build upload
