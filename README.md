# prakashsellathurai.github.io

Personal website.

## Development

```bash
# Generate static HTML pages from data files
make build

# Start a local development server
make dev

# Update data (books, github stats)
make update-data

# Run tests
make test
```

## Structure

- `data/`
    - `non-public/` - Essays (MD), books, projects, authors, site metadata
    - `public/`     - Static assets (images, fonts, favicons)
- `code/`
    - `scripts/`    - Build scripts
    - `tests/`      - Playwright tests
- `out/`            - Generated static site output (deployed to GitHub Pages)