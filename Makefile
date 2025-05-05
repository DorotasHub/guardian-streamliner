.DEFAULT_GOAL := help
VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help dev-requirements format test coverage security build deploy run-checks

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev-requirements: $(VENV)/bin/activate ## Create virtual environment and install dependencies
$(VENV)/bin/activate: dev-requirements.txt
	@test -d $(VENV) || python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r dev-requirements.txt

format: ## Autoformat code using black
	$(VENV)/bin/black src/ tests/

test: ## Run tests with pytest
	$(VENV)/bin/pytest -v tests

coverage: ## Generate code coverage report
	$(VENV)/bin/coverage run -m pytest tests/
	$(VENV)/bin/coverage report

security: ## Run security checks with bandit
	$(VENV)/bin/bandit -r src/ -ll

run-checks: format test coverage security ## Run all checks in order

build: ## Build SAM application
	sam build

deploy: ## Deploy SAM app using deploy.sh
	chmod +x deploy.sh
	./deploy.sh
