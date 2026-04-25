import fs from "fs";
import path from "path";
import matter from "gray-matter";

const DATA_DIR = path.join(process.cwd(), "data");
const PUBLIC_DIR = path.join(process.cwd(), "public");
const OUT_DIR = path.join(process.cwd(), "out");

function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function copyDir(src, dest) {
  if (!fs.existsSync(src)) return;
  ensureDir(dest);
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(path.join(DATA_DIR, file), "utf-8"));
}

function readMd(file) {
  const content = fs.readFileSync(file, "utf-8");
  return matter(content);
}

function readSiteMetadata() {
  const content = fs.readFileSync(
    path.join(DATA_DIR, "siteMetadata.js"),
    "utf-8",
  );
  const match = content.match(/const siteMetadata = (\{[\s\S]*?\n\})/);
  if (!match) return {};
  const fn = new Function("return " + match[1]);
  return fn();
}

function readAuthor() {
  const content = fs.readFileSync(
    path.join(DATA_DIR, "authors/default.mdx"),
    "utf-8",
  );
  const { data, content: body } = matter(content);
  return { ...data, body };
}

function getEssays() {
  const essaysDir = path.join(DATA_DIR, "essays");
  const files = fs.readdirSync(essaysDir).filter((f) => f.endsWith(".md"));
  return files
    .map((file) => {
      const { data, content } = readMd(path.join(essaysDir, file));
      return {
        slug: file.replace(".md", ""),
        title: data.title,
        date: data.date,
        summary: data.summary,
        tags: data.tags || [],
        content,
      };
    })
    .sort((a, b) => new Date(b.date) - new Date(a.date));
}

function getBooks() {
  return readJson("books.json");
}

function getProjects() {
  return readJson("repos.json");
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderMarkdown(content) {
  return content
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
    .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
    .replace(/^`(.+)`$/gm, "<code>$1</code>")
    .replace(/```([\s\S]+?)```/g, "<pre><code>$1</code></pre>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/^([^<]+)$/gm, (match) => {
      if (match.startsWith("<")) return match;
      return match;
    });
}

const CSS = `
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 2rem 1rem; }
a { color: #0066cc; text-decoration: none; }
a:hover { text-decoration: underline; }
header { display: flex; gap: 1.5rem; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid #eee; }
header a { font-weight: 600; }
h1 { font-size: 1.8rem; margin-bottom: 1rem; }
h2 { font-size: 1.4rem; margin: 1.5rem 0 0.5rem; }
h3 { font-size: 1.2rem; margin: 1rem 0 0.5rem; }
article { margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid #eee; }
article:last-child { border-bottom: none; }
.meta { color: #666; font-size: 0.9rem; }
.summary { color: #555; margin: 0.5rem 0; }
.tags { margin-top: 0.5rem; }
.tags a { color: #666; margin-right: 0.5rem; font-size: 0.85rem; }
.sidebar { background: #f9f9f9; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
.sidebar h3 { margin-top: 0; font-size: 1rem; }
.book-list { list-style: none; }
.book-list li { margin-bottom: 0.5rem; }
.book-list a { display: flex; justify-content: space-between; }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 0.9rem; }
@media (min-width: 700px) {
  .layout { display: flex; gap: 2rem; }
  .main { flex: 3; }
  .sidebar { flex: 1; }
}
</style>
`;

function renderHeader(metadata, nav = "") {
  return `
<header>
  <a href="/">Home</a>
  <a href="/essays/">Essays</a>
  <a href="/projects.html">Projects</a>
  <a href="/bookshelf.html">Bookshelf</a>
  <a href="/about.html">About</a>
</header>
`;
}

function renderFooter(metadata) {
  return `
<footer>
  <p>&copy; ${new Date().getFullYear()} ${escapeHtml(metadata.author)}. Built with plain HTML.</p>
</footer>
`;
}

function buildHome(metadata, essays, books, projects, author) {
  const recentEssays = essays.slice(0, 10);
  const featuredProjects = projects.slice(0, 6);
  const readingList = books["curated"]?.slice(0, 5) || [];

  let html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(metadata.title)}</title>
  <meta name="description" content="${escapeHtml(metadata.description)}">
  ${CSS}
</head>
<body>
${renderHeader(metadata)}
<div class="layout">
  <div class="main">
    <h1>Latest Essays</h1>
    ${recentEssays
      .map(
        (post) => `
    <article>
      <h2><a href="/essays/${post.slug}.html">${escapeHtml(post.title)}</a></h2>
      <p class="meta"><time>${formatDate(post.date)}</time></p>
      <p class="summary">${escapeHtml(post.summary)}</p>
      <div class="tags">
        ${post.tags
          .slice(0, 3)
          .map((tag) => `<a href="/tags/${tag}.html">#${escapeHtml(tag)}</a>`)
          .join("")}
      </div>
    </article>
    `,
      )
      .join("")}

    <h1>Featured Projects</h1>
    ${featuredProjects
      .map(
        (proj) => `
    <article>
      <h2>${proj.website ? `<a href="${escapeHtml(proj.website)}">${escapeHtml(proj.title)}</a>` : escapeHtml(proj.title)}</h2>
      <p class="summary">${escapeHtml(proj.description)}</p>
      ${proj.tags?.length ? `<div class="tags">${proj.tags.map((t) => `<span>#${escapeHtml(t)}</span>`).join("")}</div>` : ""}
    </article>
    `,
      )
      .join("")}
  </div>

  <div class="sidebar">
    <div class="sidebar">
      <h3>About ${escapeHtml(metadata.author)}</h3>
      <p>${escapeHtml(author.body.split("\n\n")[0])}</p>
      <p><a href="/about.html">Read more &rarr;</a></p>
    </div>

    <div class="sidebar">
      <h3>Reading List</h3>
      <ul class="book-list">
        ${readingList
          .map(
            (book) => `
        <li>
          <a href="${escapeHtml(book.link)}" target="_blank" rel="noopener">
            ${escapeHtml(book.title)}
          </a>
        </li>
        `,
          )
          .join("")}
      </ul>
    </div>
  </div>
</div>
${renderFooter(metadata)}
</body>
</html>`;

  fs.writeFileSync(path.join(OUT_DIR, "index.html"), html);
}

function buildEssaysList(metadata, essays) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Essays - ${escapeHtml(metadata.title)}</title>
  <meta name="description" content="Essays by ${escapeHtml(metadata.author)}">
  ${CSS}
</head>
<body>
${renderHeader(metadata)}
<h1>Essays</h1>
${essays
  .map(
    (post) => `
<article>
  <h2><a href="/essays/${post.slug}.html">${escapeHtml(post.title)}</a></h2>
  <p class="meta"><time>${formatDate(post.date)}</time></p>
  <p class="summary">${escapeHtml(post.summary)}</p>
  <div class="tags">
    ${post.tags
      .slice(0, 3)
      .map((tag) => `<a href="/tags/${tag}.html">#${escapeHtml(tag)}</a>`)
      .join("")}
  </div>
</article>
`,
  )
  .join("")}
${renderFooter(metadata)}
</body>
</html>`;

  ensureDir(path.join(OUT_DIR, "essays"));
  fs.writeFileSync(path.join(OUT_DIR, "essays", "index.html"), html);
}

function buildEssay(metadata, essay) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(essay.title)} - ${escapeHtml(metadata.title)}</title>
  <meta name="description" content="${escapeHtml(essay.summary)}">
  ${CSS}
</head>
<body>
${renderHeader(metadata)}
<article>
  <h1>${escapeHtml(essay.title)}</h1>
  <p class="meta"><time>${formatDate(essay.date)}</time></p>
  <div class="tags">
    ${essay.tags.map((tag) => `<a href="/tags/${tag}.html">#${escapeHtml(tag)}</a>`).join("")}
  </div>
  <div class="content">
    ${renderMarkdown(essay.content)}
  </div>
</article>
${renderFooter(metadata)}
</body>
</html>`;

  fs.writeFileSync(path.join(OUT_DIR, "essays", `${essay.slug}.html`), html);
}

function buildAbout(metadata, author) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>About - ${escapeHtml(metadata.title)}</title>
  <meta name="description" content="About ${escapeHtml(metadata.author)}">
  ${CSS}
</head>
<body>
${renderHeader(metadata)}
<h1>About ${escapeHtml(metadata.author)}</h1>
<h2>${escapeHtml(author.occupation)}${author.company ? ` at ${escapeHtml(author.company)}` : ""}</h2>
<div>
  ${renderMarkdown(author.body)}
</div>
${renderFooter(metadata)}
</body>
</html>`;

  fs.writeFileSync(path.join(OUT_DIR, "about.html"), html);
}

function buildProjects(metadata, projects) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Projects - ${escapeHtml(metadata.title)}</title>
  <meta name="description" content="Projects by ${escapeHtml(metadata.author)}">
  ${CSS}
</head>
<body>
${renderHeader(metadata)}
<h1>Projects</h1>
${projects
  .map(
    (proj) => `
<article>
  <h2>${proj.website ? `<a href="${escapeHtml(proj.website)}">${escapeHtml(proj.title)}</a>` : escapeHtml(proj.title)}</h2>
  <p class="summary">${escapeHtml(proj.description) || "No description"}</p>
  <p class="meta"><a href="${escapeHtml(proj.href)}">GitHub</a></p>
</article>
`,
  )
  .join("")}
${renderFooter(metadata)}
</body>
</html>`;

  fs.writeFileSync(path.join(OUT_DIR, "projects.html"), html);
}

function buildBookshelf(metadata, books) {
  const currentlyReading = books["currently-reading"] || [];
  const read = books["read"] || [];
  const curated = books["curated"] || [];

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bookshelf - ${escapeHtml(metadata.title)}</title>
  <meta name="description" content="Books I've read">
  ${CSS}
</head>
<body>
${renderHeader(metadata)}
<h1>Bookshelf</h1>

${
  currentlyReading.length
    ? `
<h2>Currently Reading</h2>
${currentlyReading
  .map(
    (book) => `
<article>
  <h3>${escapeHtml(book.title)}</h3>
  <p class="meta">by ${escapeHtml(book.author)}</p>
  <p class="summary">${escapeHtml(book.description)}</p>
</article>
`,
  )
  .join("")}
`
    : ""
}

${
  curated.length
    ? `
<h2>Curated</h2>
${curated
  .map(
    (book) => `
<article>
  <h3>${escapeHtml(book.title)}</h3>
  <p class="meta">by ${escapeHtml(book.author)}</p>
  <p class="summary">${escapeHtml(book.description)}</p>
</article>
`,
  )
  .join("")}
`
    : ""
}

${
  read.length
    ? `
<h2>Read</h2>
${read
  .map(
    (book) => `
<article>
  <h3>${escapeHtml(book.title)}</h3>
  <p class="meta">by ${escapeHtml(book.author)}</p>
  <p class="summary">${escapeHtml(book.description)}</p>
</article>
`,
  )
  .join("")}
`
    : ""
}

${renderFooter(metadata)}
</body>
</html>`;

  fs.writeFileSync(path.join(OUT_DIR, "bookshelf.html"), html);
}

function build() {
  console.log("Reading data...");
  const metadata = readSiteMetadata();
  const author = readAuthor();
  const essays = getEssays();
  const books = getBooks();
  const projects = getProjects();

  console.log(`Found ${essays.length} essays, ${projects.length} projects`);

  ensureDir(OUT_DIR);

  copyDir(PUBLIC_DIR, OUT_DIR);

  console.log("Building pages...");
  buildHome(metadata, essays, books, projects, author);
  buildEssaysList(metadata, essays);
  essays.forEach((essay) => buildEssay(metadata, essay));
  buildAbout(metadata, author);
  buildProjects(metadata, projects);
  buildBookshelf(metadata, books);

  console.log("Done! Static site generated in public/");
}

build();
