.PHONY: setup test lint security run deploy all-checks

# Setup virtual environment and install dependencies
setup:
	python -m venv venv
	. venv/bin/activate && pip install -r dev-requirements.txt

# Run all tests
test:
	pytest

# Run tests with coverage report
coverage:
	coverage run -m pytest tests/
	coverage report

# Run code formatting
lint:
	black src tests
	autopep8 --in-place --aggressive --aggressive --recursive src tests

# Run security check
security:
	bandit -r src/

# Run all checks
all-checks: lint security test coverage

# Deploy to AWS
deploy:
	chmod +x deploy.sh
	./deploy.sh

# Run locally
run:
	python -m src.cli