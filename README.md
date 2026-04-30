# prakashsellathurai.github.io

Personal website built with plain HTML.

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

- `data/` - Essays (MD), books, projects, metadata
- `public/` - static Public contents
- `scripts/` - Build scripts
- `out/` - Generated static site output