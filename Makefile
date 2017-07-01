test:
	pytest
lint:
	pycodestyle --max-line-length=100 *.py
build:
	python setup.py bdist
upload:
	twine upload -u amitbeka dist/*
