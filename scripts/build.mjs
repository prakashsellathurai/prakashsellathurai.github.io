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

function loadTemplate(templateName) {
  const templatePath = path.join(DATA_DIR, "templates", `${templateName}.html`);
  if (!fs.existsSync(templatePath)) {
    throw new Error(`Template not found: ${templatePath}`);
  }
  return fs.readFileSync(templatePath, "utf-8");
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
  
  // Load the home template
  let template = loadTemplate("home");
  
  // Replace template placeholders
  template = template.replace("{{head}}", renderHead(metadata, { title: metadata.title, description: metadata.description }));
  template = template.replace("{{header}}", renderHeader(metadata));
  template = template.replace("{{footer}}", renderFooter(metadata));
  
  // Generate recent essays HTML
  const recentEssaysHtml = recentEssays
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
    .join("");
  
  // Generate featured projects HTML
  const featuredProjectsHtml = featuredProjects
    .map(
      (proj) => `
    <article>
      <h2>${proj.website ? `<a href="${escapeHtml(proj.website)}">${escapeHtml(proj.title)}</a>` : escapeHtml(proj.title)}</h2>
      <p class="summary">${escapeHtml(proj.description)}</p>
      ${proj.tags?.length ? `<div class="tags">${proj.tags.map((t) => `<span>#${escapeHtml(t)}</span>`).join("")}</div>` : ""}
    </article>
    `,
    )
    .join("");
    
  // Generate author preview
  const authorPreview = escapeHtml(author.body.split("\n\n")[0]);
  
  // Generate reading list HTML
  const readingListHtml = readingList
    .map(
      (book) => `
    <li>
      <a href="${escapeHtml(book.link)}" target="_blank" rel="noopener">
        ${escapeHtml(book.title)}
      </a>
    </li>
    `,
    )
    .join("");
  
  // Replace content placeholders
  template = template.replace("{{recentEssays}}", recentEssaysHtml);
  template = template.replace("{{featuredProjects}}", featuredProjectsHtml);
  template = template.replace("{{authorPreview}}", authorPreview);
  template = template.replace("{{readingList}}", readingListHtml);

  fs.writeFileSync(path.join(OUT_DIR, "index.html"), template);
}

function buildEssaysList(metadata, essays) {
  // Load the essays-list template
  let template = loadTemplate("essays-list");
  
  // Replace template placeholders
  template = template.replace("{{head}}", renderHead(metadata, { title: `${metadata.title}`, description: `Essays by ${metadata.author}` }));
  template = template.replace("{{header}}", renderHeader(metadata));
  template = template.replace("{{footer}}", renderFooter(metadata));
  
  // Generate essays list HTML
  const essaysListHtml = essays
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
    .join("");
    
  // Replace content placeholder
  template = template.replace("{{essaysList}}", essaysListHtml);

  ensureDir(path.join(OUT_DIR, "essays"));
  fs.writeFileSync(path.join(OUT_DIR, "essays", "index.html"), template);
}

async function buildEssay(metadata, essay) {
  // Load the essay template
  let template = loadTemplate("essay");
  
  // Replace template placeholders
  template = template.replace("{{head}}", renderHead(metadata, { title: `${essay.title} - ${metadata.title}`, description: essay.summary }));
  template = template.replace("{{header}}", renderHeader(metadata));
  template = template.replace("{{footer}}", renderFooter(metadata));
  
  // Generate essay-specific content
  const essayTitle = escapeHtml(essay.title);
  const essayDate = formatDate(essay.date);
  const essayTags = essay.tags.map((tag) => `<a href="/tags/${tag}.html">#${escapeHtml(tag)}</a>`).join("");
  const essayContent = await renderMarkdown(essay.content);
  
  // Replace content placeholders
  template = template.replace("{{essay.title}}", essayTitle);
  template = template.replace("{{essay.date}}", essayDate);
  template = template.replace("{{essay.tags}}", essayTags);
  template = template.replace("{{essay.content}}", essayContent);

  fs.writeFileSync(path.join(OUT_DIR, "essays", `${essay.slug}.html`), template);
}

async function buildAbout(metadata, author) {
  // Load the about template
  let template = loadTemplate("about");
  
  // Replace template placeholders
  template = template.replace("{{head}}", renderHead(metadata, { title: `About - ${metadata.title}`, description: `About ${metadata.author}` }));
  template = template.replace("{{header}}", renderHeader(metadata));
  template = template.replace("{{footer}}", renderFooter(metadata));
  
  // Generate about-specific content
  const authorName = escapeHtml(metadata.author);
  const authorOccupation = escapeHtml(author.occupation);
  const authorCompany = author.company ? ` at ${escapeHtml(author.company)}` : "";
  const authorBody = await renderMarkdown(author.body);
  
  // Replace content placeholders
  template = template.replace("{{metadata.author}}", authorName);
  template = template.replace("{{author.occupation}}", authorOccupation);
  template = template.replace("{{#if author.company}} at {{author.company}}{{/if}}", authorCompany);
  template = template.replace("{{author.body}}", authorBody);

  fs.writeFileSync(path.join(OUT_DIR, "about.html"), template);
}

function buildProjects(metadata, projects) {
  // Load the projects template
  let template = loadTemplate("projects");
  
  // Replace template placeholders
  template = template.replace("{{head}}", renderHead(metadata, { title: `Projects - ${metadata.title}`, description: `Projects by ${metadata.author}` }));
  template = template.replace("{{header}}", renderHeader(metadata));
  template = template.replace("{{footer}}", renderFooter(metadata));
  
  // Generate projects list HTML
  const projectsListHtml = projects
    .map(
      (proj) => `
<article>
  <h2>${proj.website ? `<a href="${escapeHtml(proj.website)}">${escapeHtml(proj.title)}</a>` : escapeHtml(proj.title)}</h2>
  <p class="summary">${escapeHtml(proj.description) || "No description"}</p>
  <p class="meta"><a href="${escapeHtml(proj.href)}">GitHub</a></p>
</article>
`,
    )
    .join("");
    
  // Replace content placeholder
  template = template.replace("{{projectsList}}", projectsListHtml);

  fs.writeFileSync(path.join(OUT_DIR, "projects.html"), template);
}

function buildBookshelf(metadata, books) {
  const currentlyReading = books["currently-reading"] || [];
  const read = books["read"] || [];
  const curated = books["curated"] || [];

  // Load the bookshelf template
  let template = loadTemplate("bookshelf");
  
  // Replace template placeholders
  template = template.replace("{{head}}", renderHead(metadata, { title: `Bookshelf - ${metadata.title}`, description: `Books I've read` }));
  template = template.replace("{{header}}", renderHeader(metadata));
  template = template.replace("{{footer}}", renderFooter(metadata));
  
  // Generate currently reading section
  const currentlyReadingSection = currentlyReading.length
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
    : "";
    
  // Generate curated section
  const curatedSection = curated.length
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
    : "";
    
  // Generate read section
  const readSection = read.length
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
    : "";
  
  // Replace content placeholders
  template = template.replace("{{currentlyReadingSection}}", currentlyReadingSection);
  template = template.replace("{{curatedSection}}", curatedSection);
  template = template.replace("{{readSection}}", readSection);

  fs.writeFileSync(path.join(OUT_DIR, "bookshelf.html"), template);
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
  
  // Load templates
  const tagsIndexTemplate = loadTemplate("tags-index");
  const tagTemplate = loadTemplate("tag");
  
  // Build tags index page
  let tagsIndexHtml = tagsIndexTemplate
    .replace("{{head}}", renderHead(metadata, { title: `Tags - ${metadata.title}`, description: `All tags` }))
    .replace("{{header}}", renderHeader(metadata))
    .replace("{{footer}}", renderFooter(metadata))
    .replace("{{tagsCount}}", sortedTags.length)
    .replace("{{tagsList}}", sortedTags
      .map(
        ([tag, taggedEssays]) => `
    <a href="/tags/${tag}.html" class="tag">#${escapeHtml(tag)} <span class="count">${taggedEssays.length}</span></a>
    `,
      )
      .join(""));
  
  ensureDir(path.join(OUT_DIR, "tags"));
  fs.writeFileSync(path.join(OUT_DIR, "tags", "index.html"), tagsIndexHtml);

  // Build individual tag pages
  Object.entries(tagMap).forEach(([tag, taggedEssays]) => {
    const tagHtml = tagTemplate
      .replace("{{head}}", renderHead(metadata, { title: `#${tag} - ${metadata.title}`, description: `Essays tagged with ${tag}` }))
      .replace("{{header}}", renderHeader(metadata))
      .replace("{{footer}}", renderFooter(metadata))
      .replace("{{tag}}", escapeHtml(tag))
      .replace("{{taggedEssaysCount}}", taggedEssays.length)
      .replace("{{#if taggedEssaysCount}}s{{/if}}", taggedEssays.length !== 1 ? "s" : "")
      .replace("{{taggedEssays}}", taggedEssays
        .map(
          (post) => `
<article>
  <h2><a href="/essays/${post.slug}.html">${escapeHtml(post.title)}</a></h2>
  <p class="meta"><time>${formatDate(post.date)}</time></p>
  <p class="summary">${escapeHtml(post.summary)}</p>
</article>
`,
        )
        .join(""));
    
    fs.writeFileSync(path.join(OUT_DIR, "tags", `${tag}.html`), tagHtml);
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

  console.log("Generating RSS and sitemap...");
  fs.writeFileSync(path.join(OUT_DIR, "feed.xml"), generateRssFeed(metadata, essays));
  fs.writeFileSync(path.join(OUT_DIR, "sitemap.xml"), generateSitemap(metadata, essays, projects, leetcodeSolutions));

  console.log("Done! Static site generated in out/");
}

build();
