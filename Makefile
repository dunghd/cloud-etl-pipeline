# Makefile for Cloud ETL Pipeline

.PHONY: install setup test lint format clean run help

# Variables
PYTHON := poetry run python
PYTEST := poetry run pytest
BLACK := poetry run black
FLAKE8 := poetry run flake8
MYPY := poetry run mypy

help:
	@echo "Cloud ETL Pipeline - Makefile Commands"
	@echo "======================================"
	@echo "install     - Install dependencies with Poetry"
	@echo "setup       - Initial setup (install + configure)"
	@echo "test        - Run unit tests"
	@echo "test-cov    - Run tests with coverage report"
	@echo "lint        - Run linting checks"
	@echo "format      - Format code with Black"
	@echo "type-check  - Run type checking with mypy"
	@echo "clean       - Clean temporary files and caches"
	@echo "run         - Run example pipeline"
	@echo "shell       - Activate Poetry shell"

install:
	@echo "Installing dependencies..."
	poetry install

setup: install
	@echo "Setting up project..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created. Please update with your credentials."; \
	fi
	@mkdir -p logs data/raw data/processed

test:
	@echo "Running tests..."
	$(PYTEST)

test-cov:
	@echo "Running tests with coverage..."
	$(PYTEST) --cov=etl --cov-report=html --cov-report=term-missing

lint:
	@echo "Running linting..."
	$(FLAKE8) etl/ tests/

format:
	@echo "Formatting code..."
	$(BLACK) etl/ tests/ examples.py

type-check:
	@echo "Running type checks..."
	$(MYPY) etl/

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	rm -rf spark-warehouse metastore_db derby.log

run:
	@echo "Running example pipeline..."
	$(PYTHON) examples.py

shell:
	@echo "Activating Poetry shell..."
	poetry shell
