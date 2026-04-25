# prakashsellathurai.github.io

Personal website built with plain HTML.

## Development

```bash
# Generate static HTML pages from data files
bun run build

# Update data (books, github stats)
bun run update-data
```

## Structure

- `data/` - Essays (MD), books, projects, metadata
- `public/` - Generated static HTML pages
- `scripts/` - Build scripts