import fs from "fs";
import path from "path";
import matter from "gray-matter";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import remarkRehype from "remark-rehype";
import rehypeStringify from "rehype-stringify";
import { remarkSideNotes } from "./remark-side-notes.mjs";

const DATA_DIR = path.join(process.cwd(), "data");
const PUBLIC_DIR = path.join(process.cwd(), "public");
const OUT_DIR = path.join(process.cwd(), "out");

function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function clearDir(dir) {
  if (!fs.existsSync(dir)) return;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const entryPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      fs.rmSync(entryPath, { recursive: true });
    } else {
      fs.unlinkSync(entryPath);
    }
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
      if (data.draft) return null;
      return {
        slug: file.replace(".md", ""),
        title: data.title,
        date: data.date,
        summary: data.summary,
        tags: data.tags || [],
        content,
      };
    })
    .filter(Boolean)
    .sort((a, b) => new Date(b.date) - new Date(a.date));
}

function getBooks() {
  return readJson("books.json");
}

function getProjects() {
  return readJson("repos.json");
}

function getLeetcodeSolutions() {
  return readJson("leetcode-solutions.json");
}

function formatDateISO(dateStr) {
  const date = new Date(dateStr);
  return date.toISOString().split('T')[0];
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function generateSitemap(metadata, essays, projects, leetcodeSolutions) {
  const siteUrl = metadata.siteUrl.replace(/\/$/, '');
  const today = new Date().toISOString().split('T')[0];

  const tagSet = new Set();
  essays.forEach((e) => e.tags.forEach((t) => tagSet.add(t)));
  const tagEntries = [...tagSet].map((t) => ({
    loc: `/tags/${t}.html`,
    lastmod: today,
    priority: '0.6',
  }));

  const pages = [
    { loc: '/', lastmod: today, priority: '1.0' },
    { loc: '/essays/', lastmod: today, priority: '0.9' },
    { loc: '/about.html', lastmod: today, priority: '0.9' },
    { loc: '/tags/', lastmod: today, priority: '0.8' },
    { loc: '/projects.html', lastmod: today, priority: '0.8' },
    { loc: '/bookshelf.html', lastmod: today, priority: '0.8' },
    { loc: '/leetcode-solutions/', lastmod: today, priority: '0.6' },
    { loc: '/static/resume/prakash_s_resume.pdf', lastmod: today, priority: '0.7' },
  ];

  const essayEntries = essays.map((e) => ({
    loc: `/essays/${e.slug}.html`,
    lastmod: formatDateISO(e.date),
    priority: '0.7',
  }));

  const projectEntries = projects
    .filter((p) => p.website && p.website.startsWith('http'))
    .map((p) => ({
      loc: p.website,
      lastmod: today,
      priority: '0.6',
    }));

  const leetcodeEntries = leetcodeSolutions.map((s) => ({
    loc: s.href,
    lastmod: today,
    priority: '0.5',
  }));

  const urls = [...pages, ...essayEntries, ...tagEntries, ...projectEntries, ...leetcodeEntries]
    .map((p) => `  <url>\n    <loc>${siteUrl}${p.loc}</loc>\n    <lastmod>${p.lastmod}</lastmod>\n    <priority>${p.priority}</priority>\n  </url>`)
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>`;
}

function generateRssFeed(metadata, essays) {
  const siteUrl = metadata.siteUrl.replace(/\/$/, '');
  const sortedEssays = [...essays].sort((a, b) => new Date(b.date) - new Date(a.date));

  const items = sortedEssays
    .map(
      (e) => `  <item>
    <guid>${siteUrl}/essays/${e.slug}.html</guid>
    <title><![CDATA[${e.title}]]></title>
    <link>${siteUrl}/essays/${e.slug}.html</link>
    <description><![CDATA[${e.summary || ''}]]></description>
    <pubDate>${new Date(e.date).toUTCString()}</pubDate>
  </item>`,
    )
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title><![CDATA[${metadata.title}]]></title>
    <link>${siteUrl}</link>
    <description><![CDATA[${metadata.description}]]></description>
    <language>${metadata.language}</language>
    <lastBuildDate>${new Date(sortedEssays[0]?.date).toUTCString()}</lastBuildDate>
    <atom:link href="${siteUrl}/feed.xml" rel="self" type="application/rss+xml"/>
${items}
  </channel>
</rss>`;
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

async function renderMarkdown(content) {
  const result = await unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkSideNotes)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(rehypeStringify)
    .process(content);
  return String(result);
}



const CSS_LINK = '<link rel="stylesheet" href="/static/css/style.css">';

function renderHead(metadata, { title, description }) {
  return `
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(title)}</title>
  <meta name="description" content="${escapeHtml(description)}">
  ${CSS_LINK}
</head>
`;
}

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
${renderHead(metadata, { title: metadata.title, description: metadata.description })}
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
${renderHead(metadata, { title: `${metadata.title}`, description: `Essays by ${metadata.author}` })}
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

async function buildEssay(metadata, essay) {
  const html = `<!DOCTYPE html>
<html lang="en">
${renderHead(metadata, { title: `${essay.title} - ${metadata.title}`, description: essay.summary })}
<body>
${renderHeader(metadata)}
<article>
  <h1>${escapeHtml(essay.title)}</h1>
  <p class="meta"><time>${formatDate(essay.date)}</time></p>
  <div class="tags">
    ${essay.tags.map((tag) => `<a href="/tags/${tag}.html">#${escapeHtml(tag)}</a>`).join("")}
  </div>
  <div class="content">
    ${await renderMarkdown(essay.content)}
  </div>
</article>
${renderFooter(metadata)}
</body>
</html>`;

  fs.writeFileSync(path.join(OUT_DIR, "essays", `${essay.slug}.html`), html);
}

async function buildAbout(metadata, author) {
  const html = `<!DOCTYPE html>
<html lang="en">
${renderHead(metadata, { title: `About - ${metadata.title}`, description: `About ${metadata.author}` })}
<body>
${renderHeader(metadata)}
<h1>About ${escapeHtml(metadata.author)}</h1>
<h2>${escapeHtml(author.occupation)}${author.company ? ` at ${escapeHtml(author.company)}` : ""}</h2>
<div>
  ${await renderMarkdown(author.body)}
</div>
${renderFooter(metadata)}
</body>
</html>`;

  fs.writeFileSync(path.join(OUT_DIR, "about.html"), html);
}

function buildProjects(metadata, projects) {
  const html = `<!DOCTYPE html>
<html lang="en">
${renderHead(metadata, { title: `Projects - ${metadata.title}`, description: `Projects by ${metadata.author}` })}
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
${renderHead(metadata, { title: `Bookshelf - ${metadata.title}`, description: `Books I've read` })}
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

function buildLeetcodeSolutions(metadata, solutions) {
  const html = `<!DOCTYPE html>
<html lang="en">
${renderHead(metadata, { title: `Leetcode Solutions - ${metadata.title}`, description: `My solutions to Leetcode problems` })}
<body>
${renderHeader(metadata)}
<h1>Leetcode Solutions</h1>
<p class="meta">${solutions.length} solutions</p>
${solutions
  .map(
    (solution) => `
<article>
  <h2><a href="${escapeHtml(solution.href)}">${escapeHtml(solution.title)}</a></h2>
</article>
`,
  )
  .join("")}
${renderFooter(metadata)}
</body>
</html>`;

  ensureDir(path.join(OUT_DIR, "leetcode-solutions"));
  fs.writeFileSync(path.join(OUT_DIR, "leetcode-solutions", "index.html"), html);
}

function buildTags(metadata, essays) {
  const tagMap = {};
  essays.forEach((essay) => {
    essay.tags.forEach((tag) => {
      if (!tagMap[tag]) tagMap[tag] = [];
      tagMap[tag].push(essay);
    });
  });

  const sortedTags = Object.entries(tagMap).sort((a, b) => b[1].length - a[1].length);

  const tagsIndexHtml = `<!DOCTYPE html>
<html lang="en">
${renderHead(metadata, { title: `Tags - ${metadata.title}`, description: `All tags` })}
<body>
${renderHeader(metadata)}
<h1>Tags</h1>
<p class="meta">${sortedTags.length} tags</p>
<div class="tags-cloud">
  ${sortedTags
    .map(
      ([tag, taggedEssays]) => `
    <a href="/tags/${tag}.html" class="tag">#${escapeHtml(tag)} <span class="count">${taggedEssays.length}</span></a>
  `,
    )
    .join("")}
</div>
${renderFooter(metadata)}
</body>
</html>`;

  ensureDir(path.join(OUT_DIR, "tags"));
  fs.writeFileSync(path.join(OUT_DIR, "tags", "index.html"), tagsIndexHtml);

  Object.entries(tagMap).forEach(([tag, taggedEssays]) => {
    const html = `<!DOCTYPE html>
<html lang="en">
${renderHead(metadata, { title: `#${tag} - ${metadata.title}`, description: `Essays tagged with ${tag}` })}
<body>
${renderHeader(metadata)}
<h1>#${escapeHtml(tag)}</h1>
<p class="meta">${taggedEssays.length} essay${taggedEssays.length !== 1 ? "s" : ""}</p>
${taggedEssays
  .map(
    (post) => `
<article>
  <h2><a href="/essays/${post.slug}.html">${escapeHtml(post.title)}</a></h2>
  <p class="meta"><time>${formatDate(post.date)}</time></p>
  <p class="summary">${escapeHtml(post.summary)}</p>
</article>
`,
  )
  .join("")}
${renderFooter(metadata)}
</body>
</html>`;

    fs.writeFileSync(path.join(OUT_DIR, "tags", `${tag}.html`), html);
  });
}

async function build() {
  console.log("Reading data...");
  const metadata = readSiteMetadata();
  const author = readAuthor();
  const essays = getEssays();
  const books = getBooks();
  const projects = getProjects();
  const leetcodeSolutions = getLeetcodeSolutions();

  console.log(`Found ${essays.length} essays, ${projects.length} projects, ${leetcodeSolutions.length} leetcode solutions`);

  ensureDir(OUT_DIR);
  clearDir(OUT_DIR);

  copyDir(PUBLIC_DIR, OUT_DIR);

  console.log("Building pages...");
  buildHome(metadata, essays, books, projects, author);
  buildEssaysList(metadata, essays);
  for (const essay of essays) {
    await buildEssay(metadata, essay);
  }
  buildTags(metadata, essays);
  await buildAbout(metadata, author);
  buildProjects(metadata, projects);
  buildBookshelf(metadata, books);
  buildLeetcodeSolutions(metadata, leetcodeSolutions);

  console.log("Generating RSS and sitemap...");
  fs.writeFileSync(path.join(OUT_DIR, "feed.xml"), generateRssFeed(metadata, essays));
  fs.writeFileSync(path.join(OUT_DIR, "sitemap.xml"), generateSitemap(metadata, essays, projects, leetcodeSolutions));

  console.log("Done! Static site generated in out/");
}

build();
