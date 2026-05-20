import { existsSync, mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { slug } from '../lib/slug.mjs'

const ROOT = process.cwd()
const ESSAYS_DIR = path.join(ROOT, 'data','non-public' , 'essays')

const templates = {
  default: () => `
`,
  opinion: () => `## Thesis
<!-- Your point of view in one sentence. -->

## Why It Matters
<!-- Stakes, consequences, or relevance. -->

## The Case
<!-- 2-4 key arguments with examples. -->

## Counterpoints
<!-- Address the strongest objections. -->

## Takeaway
<!-- What should the reader do or think next? -->
`,
  howto: () => `## Goal
<!-- What the reader will achieve. -->

## Prerequisites
<!-- Tools, knowledge, or setup required. -->

## Steps
1.
2.
3.

## Gotchas
<!-- Common pitfalls and fixes. -->

## Next
<!-- Variations or deeper topics. -->
`,
  review: () => `## Summary
<!-- What is this, in one paragraph? -->

## What Worked
<!-- Strengths and standout moments. -->

## What Didn’t
<!-- Weaknesses or gaps. -->

## Who It’s For
<!-- Ideal audience or use case. -->

## Verdict
<!-- Final rating or recommendation. -->
`,
  research: () => `## Question
<!-- What are you trying to answer? -->

## Method
<!-- How you explored or tested it. -->

## Findings
<!-- Key results or observations. -->

## Implications
<!-- Why the findings matter. -->

## Open Questions
<!-- What remains unresolved. -->
`,
}

const usage = () => {
  console.log(`Usage:
  bun ./scripts/utils/create-essay.mjs --title "My New Essay" [options]

Options:
  --slug "custom-slug"       Optional custom slug (defaults to title)
  --template default         default | opinion | howto | review | research
  --tags "tag1,tag2"         Comma-separated tags
  --summary "Short summary"  Summary shown in lists
  --authors "default"        Comma-separated authors (default: "default")
  --layout "PostLayout"      Optional layout override
  --publish                  Sets draft to false (default is true)
  --ext "md"                 File extension (md or mdx)
`)
}

const parseArgs = (argv) => {
  const args = {}
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    if (!arg.startsWith('--')) continue
    const key = arg.slice(2)
    const next = argv[i + 1]
    if (next && !next.startsWith('--')) {
      args[key] = next
      i += 1
    } else {
      args[key] = true
    }
  }
  return args
}

const args = parseArgs(process.argv.slice(2))
const title = args.title

if (!title) {
  usage()
  process.exit(1)
}

if (!existsSync(ESSAYS_DIR)) {
  mkdirSync(ESSAYS_DIR, { recursive: true })
}

const templateKey = (args.template || 'default').toLowerCase()
const template = templates[templateKey]
if (!template) {
  console.error(`Unknown template: ${templateKey}`)
  console.error(`Available: ${Object.keys(templates).join(', ')}`)
  process.exit(1)
}

const resultSlug = args.slug ? String(args.slug) : slug(String(title))
const ext = (args.ext || 'md').toLowerCase()
const draft = args.publish ? false : true

const tags = args.tags
  ? String(args.tags)
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean)
  : []

const authors = args.authors
  ? String(args.authors)
      .split(',')
      .map((author) => author.trim())
      .filter(Boolean)
  : ['default']

const summary = args.summary ? String(args.summary) : ''
const layout = args.layout ? String(args.layout) : ''

const date = new Date().toISOString()

const frontmatter = [
  '---',
  `title: ${JSON.stringify(String(title))}`,
  `date: '${date}'`,
  `draft: ${draft ? 'true' : 'false'}`,
  `tags: ${JSON.stringify(tags)}`,
  `summary: ${JSON.stringify(summary)}`,
  `authors: ${JSON.stringify(authors)}`,
  layout ? `layout: ${JSON.stringify(layout)}` : null,
  '---',
  '',
]
  .filter(Boolean)
  .join('\n')

let filename = `${resultSlug}.${ext}`
let targetPath = path.join(ESSAYS_DIR, filename)
let counter = 1
while (existsSync(targetPath)) {
  filename = `${resultSlug}-${counter}.${ext}`
  targetPath = path.join(ESSAYS_DIR, filename)
  counter += 1
}

const body = template()
writeFileSync(targetPath, `${frontmatter}\n${body}`, 'utf8')

console.log(`Created: ${path.relative(ROOT, targetPath)}`)
