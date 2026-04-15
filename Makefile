.PHONY: run test lint format install

run:
	python manage.py runserver

test:
	DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test --verbosity=2

lint:
	ruff check .

format:
	ruff format .

install:
	python -m pip install -r requirements.txt ruff pre-commit
	pre-commit install
