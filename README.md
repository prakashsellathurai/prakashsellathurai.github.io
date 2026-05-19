# prakashsellathurai.github.io

Personal website.

## Development

```bash
# Generate static HTML pages from data files
bun run build

# Start a local development server
bun run dev

# Update data (books, github stats)
bun run update-data
```

## Structure

- `data/`
    - `non-public/` - Essays (MD), books, projects, authors, site metadata
    - `public/`     - Static assets (images, fonts, favicons)
- `code/`
    - `scripts/`    - Build scripts
    - `test/`       - Playwright tests
- `out/`            - Generated static site output (deployed to GitHub Pages)