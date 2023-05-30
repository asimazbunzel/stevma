# module installation
.PHONY: install
install:
	pip install .

# set up python interpreter environment
.PHONY: dev
dev:
	@echo "creating dev environment"
	conda env create -f environment.yml

# setup pre-commit for devs
.PHONY: pre-commit-install
pre-commit-install:
	pre-commit install

# formatters
.PHONY: codestyle
codestyle:
	isort --settings-path pyproject.toml ./
	black --config pyproject.toml ./
	flake8 ./ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 ./ --count --exit-zero --max-complexity=50 --max-line-length=127 --statistics
	# pyupgrade --exit-zero-even-if-changed --py37-plus **/*.py

.PHONY: formatting
formatting: codestyle

# linting
.PHONY: test
test:
	@echo "not ready to test"

.PHONY: mypy
mypy:
	mypy --config-file pyproject.toml ./

.PHONY: check-safety
check-safety:
	safety check --full-report
	bandit -ll --recursive stevdb tests

.PHONY: lint
lint: test check-codestyle mypy check-safety

## delete all compiled python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
