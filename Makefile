.PHONY: build dev test test-ui update-data install-dev install-playwright clean

BUNX = bunx
# Check if uv is installed, otherwise install it
UV := $(shell command -v uv 2> /dev/null)

all: install

install:
	@if command -v uv > /dev/null 2>&1; then \
		uv sync; \
	else \
		echo "uv not found. Installing..."; \
		curl -LsSf https://astral.sh | sh; \
		$(HOME)/.local/bin/uv sync; \
	fi

build:
	uv run  code/scripts/build.py

dev: build
	uvx ssserve ./out

test:
	uv run pytest code/tests/ -v

test-ui:
	uv run pytest code/tests/ -v --headed

update-data:
	uv run python3 code/scripts/utils/books.py
	uv run python3 code/scripts/utils/github.py
	uv run python3 code/scripts/utils/quotes.py
	uv run python3 code/scripts/utils/sync_description.py

install-dev:
	uv sync --group dev

install-playwright:
	uv run playwright install --with-deps chromium

clean:
	rm -rf out .venv
