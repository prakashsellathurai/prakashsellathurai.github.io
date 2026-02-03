import fs from 'fs'
import path from 'path'

const authorPath = path.join(__dirname, '../data/authors/default.mdx')
const siteMetadataPath = path.join(__dirname, '../data/siteMetadata.js')

// Read author file
const file = fs.readFileSync(authorPath, 'utf8')
// Remove frontmatter
const content = file.replace(/---[\s\S]*?---/, '').trim()
// Get first non-empty paragraph
const paragraphs = content
  .split(/\n\n+/)
  .map((p) => p.trim())
  .filter(Boolean)
const firstParagraph = paragraphs.length > 0 ? paragraphs[0] : ''

// Read siteMetadata.js
let siteMetadataSrc = fs.readFileSync(siteMetadataPath, 'utf8')

// Replace the description field (assumes it is a single- or multi-line string)
siteMetadataSrc = siteMetadataSrc.replace(
  /description:\s*([`'"])([\s\S]*?)(\1),/,
  `description: '${firstParagraph.replace(/'/g, "\\'")}',`
)

fs.writeFileSync(siteMetadataPath, siteMetadataSrc)
console.log('siteMetadata.js description updated from default.mdx')
