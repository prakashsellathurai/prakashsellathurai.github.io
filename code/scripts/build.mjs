import fs from "fs";
import path from "path";
import matter from "gray-matter";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import remarkRehype from "remark-rehype";
import rehypeStringify from "rehype-stringify";
import { remarkSideNotes } from "./remark-side-notes.mjs";
import { console } from "inspector/promises";

class FileSystem {
  static ensureDir(dir) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  static clearDir(dir) {
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

  static copyDir(src, dest) {
    if (!fs.existsSync(src)) return;
    FileSystem.ensureDir(dest);
    for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
      const srcPath = path.join(src, entry.name);
      const destPath = path.join(dest, entry.name);
      if (entry.isDirectory()) {
        FileSystem.copyDir(srcPath, destPath);
      } else {
        fs.copyFileSync(srcPath, destPath);
      }
    }
  }

  static read(file) {
    return fs.readFileSync(file, "utf-8");
  }

  static write(file, content) {
    fs.writeFileSync(file, content);
  }

  static exists(file) {
    return fs.existsSync(file);
  }
}

class DataLoader {
  constructor(dataDir) {
    this.dataDir = dataDir;
  }

  readJson(file) {
    return JSON.parse(FileSystem.read(path.join(this.dataDir, file)));
  }

  readMd(file) {
    const content = FileSystem.read(file);
    return matter(content);
  }

  loadTemplate(templateName) {
    const templatePath = path.join(this.dataDir, "templates", `${templateName}.html`);
    if (!FileSystem.exists(templatePath)) {
      throw new Error(`Template not found: ${templatePath}`);
    }
    return FileSystem.read(templatePath);
  }

  readAuthor() {
    const content = FileSystem.read(path.join(this.dataDir, "authors/default.mdx"));
    const { data, content: body } = matter(content);
    return { ...data, body };
  }

  readSiteMetadata() {
    const content = FileSystem.read(path.join(this.dataDir, "siteMetadata.js"), "utf-8");
    const match = content.match(/const siteMetadata = (\{[\s\S]*?\n\})/);
    if (!match) return {};
    const fn = new Function("return " + match[1]);
    return fn();
  }

  getEssays() {
    const essaysDir = path.join(this.dataDir, "essays");
    const files = fs.readdirSync(essaysDir).filter((f) => f.endsWith(".md"));
    return files
      .map((file) => {
        const { data, content } = this.readMd(path.join(essaysDir, file));
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

  getBooks() {
    return this.readJson("books.json");
  }

  getProjects() {
    return this.readJson("repos.json");
  }

  getLeetcodeSolutions() {
    return this.readJson("leetcode-solutions.json");
  }
}

class Formatter {
  static formatDateISO(dateStr) {
    const date = new Date(dateStr);
    return date.toISOString().split('T')[0];
  }

  static formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  static escapeHtml(text) {
    if (!text) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
}

class MarkdownRenderer {
  constructor() {
    this.processor = unified()
      .use(remarkParse)
      .use(remarkGfm)
      .use(remarkSideNotes)
      .use(remarkRehype, { allowDangerousHtml: true })
      .use(rehypeStringify);
  }

  async render(content) {
    const result = await this.processor.process(content);
    return String(result);
  }
}

class TemplateRenderer {
  static renderHead(metadata, { title, description, url = '', image = '' }) {
    const siteUrl = metadata.siteUrl.replace(/\/$/, '');
    const fullUrl = url ? `${siteUrl}${url}` : siteUrl;
    const ogImage = image || metadata.socialBanner || metadata.siteLogo;
    const keywords = metadata.keywords?.join(', ') || '';

    const canonical = `<link rel="canonical" href="${fullUrl}">`;
    const keywordsMeta = keywords ? `<meta name="keywords" content="${Formatter.escapeHtml(keywords)}">` : '';
    const openGraph = `
  <meta property="og:title" content="${Formatter.escapeHtml(title)}">
  <meta property="og:description" content="${Formatter.escapeHtml(description)}">
  <meta property="og:url" content="${fullUrl}">
  <meta property="og:image" content="${siteUrl}${ogImage}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="${Formatter.escapeHtml(metadata.title)}">`;
    const twitterCard = `
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="${Formatter.escapeHtml(title)}">
  <meta name="twitter:description" content="${Formatter.escapeHtml(description)}">
  <meta name="twitter:image" content="${siteUrl}${ogImage}">`;
    const jsonLd = `
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "${Formatter.escapeHtml(metadata.author)}",
    "url": "${siteUrl}",
    "sameAs": ${JSON.stringify(metadata.authorDetails?.sameAs || [])},
    "jobTitle": "${Formatter.escapeHtml(metadata.authorDetails?.jobTitle || 'Software Engineer')}",
    "description": "${Formatter.escapeHtml(metadata.description)}"
  }
  </script>`;

    const cssLink = '<link rel="stylesheet" href="/static/css/style.css">';
    const favicon = `
  <link rel="apple-touch-icon" sizes="180x180" href="/static/favicons/apple-touch-icon.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/static/favicons/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/static/favicons/favicon-16x16.png">
  <link rel="manifest" href="/static/favicons/site.webmanifest">
  <link rel="mask-icon" href="/static/favicons/safari-pinned-tab.svg" color="#8b7355">`;
    const rssLink = `<link rel="alternate" type="application/rss+xml" title="${Formatter.escapeHtml(metadata.title)}" href="${siteUrl}/feed.xml">`;
    return `
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${Formatter.escapeHtml(title)}</title>
  <meta name="description" content="${Formatter.escapeHtml(description)}">
  ${keywordsMeta}
  ${canonical}
  ${openGraph}
  ${twitterCard}
  ${jsonLd}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap" rel="stylesheet">
  ${rssLink}
  ${favicon}
  ${cssLink}
</head>
`;
  }

  static renderHeader(metadata) {
    return `
<header>
  <a href="/">Home</a>
  <a href="/static/resume/prakash_s_resume.pdf">Resume</a>
  <a href="/essays/">Essays</a>
  <a href="/projects.html">Projects</a>
  <a href="/bookshelf.html">Bookshelf</a>
  <a href="/about.html">About</a>
  <a href="/feed.xml" class="rss-link" aria-label="RSS Feed">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4 11a9 9 0 0 1 9 9"/>
      <path d="M4 4a16 16 0 0 1 16 16"/>
      <circle cx="5" cy="19" r="1"/>
    </svg>
  </a>
</header>
`;
  }

  static renderFooter(metadata) {
    return `
<footer>
  <p>&copy; ${new Date().getFullYear()} ${Formatter.escapeHtml(metadata.author)}.</p>
</footer>
`;
  }

  static apply(template, data) {
    let result = template;
    for (const [key, value] of Object.entries(data)) {
      if (value !== undefined) {
        result = result.replace(new RegExp(`{{${key}}}`, 'g'), value);
      }
    }
    return result;
  }
}

class FeedGenerator {
  static generateSitemap(metadata, essays, projects, leetcodeSolutions) {
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
      lastmod: Formatter.formatDateISO(e.date),
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

  static generateRssFeed(metadata, essays) {
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
}

class PageBuilder {
  constructor(dataLoader, markdownRenderer) {
    this.dataLoader = dataLoader;
    this.markdownRenderer = markdownRenderer;
  }

  buildCommon(template, metadata, pageTitle, pageDescription, url = '', image = '') {
    return TemplateRenderer.apply(template, {
      head: TemplateRenderer.renderHead(metadata, { title: pageTitle, description: pageDescription, url, image }),
      header: TemplateRenderer.renderHeader(metadata),
      footer: TemplateRenderer.renderFooter(metadata),
    });
  }

  async buildHome(metadata, essays, books, projects, author, avatar) {
    const template = this.dataLoader.loadTemplate("home");
    let html = this.buildCommon(template, metadata, metadata.title, metadata.description, '/');

    const recentEssaysHtml = essays.slice(0, 10).map((post) => `
    <article>
      <h2><a href="/essays/${post.slug}.html">${Formatter.escapeHtml(post.title)}</a></h2>
      <p class="meta"><time>${Formatter.formatDate(post.date)}</time></p>
      <p class="summary">${Formatter.escapeHtml(post.summary)}</p>
      <div class="tags">
        ${post.tags.slice(0, 3).map((tag) => `<a href="/tags/${tag}.html">#${Formatter.escapeHtml(tag)}</a>`).join("")}
      </div>
    </article>`).join("") + `
    <p class="section-footer"><a href="/essays/">All essays &rarr;</a></p>`;

    const featuredProjectsHtml = `
    <div class="project-grid">` +
    projects.slice(0, 6).map((proj) => `
    <div class="project-card">
      <h3>${proj.website ? `<a href="${Formatter.escapeHtml(proj.website)}">${Formatter.escapeHtml(proj.title)}</a>` : Formatter.escapeHtml(proj.title)}</h3>
      <p class="summary">${Formatter.escapeHtml(proj.description)}</p>
      ${proj.tags?.length ? `<div class="tags">${proj.tags.map((t) => `<span>#${Formatter.escapeHtml(t)}</span>`).join("")}</div>` : ""}
    </div>`).join("") + `
    </div>
    <p class="section-footer"><a href="/projects.html">All projects &rarr;</a></p>`;

    const readingListHtml = (books["curated"] || []).slice(0, 5).map((book) => `
    <li>
      <a href="${Formatter.escapeHtml(book.link)}" target="_blank" rel="noopener">${Formatter.escapeHtml(book.title)}</a>
    </li>`).join("");

    html = TemplateRenderer.apply(html, {
      recentEssays: recentEssaysHtml,
      featuredProjects: featuredProjectsHtml,
      authorPreview: Formatter.escapeHtml(author.body.split("\n\n")[0]),
      readingList: readingListHtml,
      "metadata.author": Formatter.escapeHtml(metadata.author),
      avatar: avatar,
    });

    FileSystem.write(path.join(process.cwd(), "out", "index.html"), html);
  }

  async buildEssaysList(metadata, essays) {
    const template = this.dataLoader.loadTemplate("essays-list");
    let html = this.buildCommon(template, metadata, metadata.title, `Essays by ${metadata.author}`, '/essays/');

    const essaysListHtml = essays.map((post) => `
<article>
  <h2><a href="/essays/${post.slug}.html">${Formatter.escapeHtml(post.title)}</a></h2>
  <p class="meta"><time>${Formatter.formatDate(post.date)}</time></p>
  <p class="summary">${Formatter.escapeHtml(post.summary)}</p>
  <div class="tags">
    ${post.tags.slice(0, 3).map((tag) => `<a href="/tags/${tag}.html">#${Formatter.escapeHtml(tag)}</a>`).join("")}
  </div>
</article>`).join("");

    html = TemplateRenderer.apply(html, { essaysList: essaysListHtml });

    FileSystem.ensureDir(path.join(process.cwd(), "out", "essays"));
    FileSystem.write(path.join(process.cwd(), "out", "essays", "index.html"), html);
  }

  async buildEssay(metadata, essay) {
    const template = this.dataLoader.loadTemplate("essay");
    let html = this.buildCommon(template, metadata, `${essay.title} - ${metadata.title}`, essay.summary, `/essays/${essay.slug}.html`);

    const essayContent = await this.markdownRenderer.render(essay.content);

    html = TemplateRenderer.apply(html, {
      "essay.title": Formatter.escapeHtml(essay.title),
      "essay.date": Formatter.formatDate(essay.date),
      "essay.tags": essay.tags.map((tag) => `<a href="/tags/${tag}.html">#${Formatter.escapeHtml(tag)}</a>`).join(""),
      "essay.content": essayContent,
    });

    FileSystem.write(path.join(process.cwd(), "out", "essays", `${essay.slug}.html`), html);
  }

  async buildAbout(metadata, author, avatar) {
    const template = this.dataLoader.loadTemplate("about");
    let html = this.buildCommon(template, metadata, `About - ${metadata.title}`, `About ${metadata.author}`, '/about.html');

    const authorBody = await this.markdownRenderer.render(author.body);

    html = TemplateRenderer.apply(html, {
      "metadata.author": Formatter.escapeHtml(metadata.author),
      "author.occupation": Formatter.escapeHtml(author.occupation),
      "author.body": authorBody,
      avatar: avatar,
    });

    FileSystem.write(path.join(process.cwd(), "out", "about.html"), html);
  }

  buildProjects(metadata, projects) {
    const template = this.dataLoader.loadTemplate("projects");
    let html = this.buildCommon(template, metadata, `Projects - ${metadata.title}`, `Projects by ${metadata.author}`, '/projects.html');

    const projectsListHtml = `
    <div class="project-grid">` +
    projects.map((proj) => `
    <div class="project-card">
      <h3>${proj.website ? `<a href="${Formatter.escapeHtml(proj.website)}">${Formatter.escapeHtml(proj.title)}</a>` : Formatter.escapeHtml(proj.title)}</h3>
      <p class="summary">${Formatter.escapeHtml(proj.description)}</p>
      ${proj.tags?.length ? `<div class="tags">${proj.tags.map((t) => `<span>#${Formatter.escapeHtml(t)}</span>`).join("")}</div>` : ""}
      <p class="meta"><a href="${Formatter.escapeHtml(proj.href)}">GitHub</a></p>
    </div>`).join("") + `
    </div>`;

    html = TemplateRenderer.apply(html, { projectsList: projectsListHtml });

    FileSystem.write(path.join(process.cwd(), "out", "projects.html"), html);
  }

  buildBookshelf(metadata, books) {
    const template = this.dataLoader.loadTemplate("bookshelf");
    let html = this.buildCommon(template, metadata, `Bookshelf - ${metadata.title}`, `Books I've read`, '/bookshelf.html');

    const curated = books["curated"] || [];
    const curatedKeys = new Set(curated.map((b) => b.title + "||" + b.author));
    const readBooks = (books["read"] || []).filter((b) => !curatedKeys.has(b.title + "||" + b.author));

    const titleColor = (title) => {
      let hash = 0;
      for (let i = 0; i < title.length; i++) {
        hash = title.charCodeAt(i) + ((hash << 5) - hash);
      }
      return `hsl(${Math.abs(hash) % 360}, 50%, 45%)`;
    };

    const renderStars = (rating) => {
      const n = parseInt(rating, 10);
      if (!n || n === 0) return "";
      return "★".repeat(n) + "☆".repeat(5 - n);
    };

    const isPlaceholderCover = (url) => !url || url.includes("nophoto");

    const buildBookCard = (book) => {
      const escapedTitle = Formatter.escapeHtml(book.title);
      const escapedAuthor = Formatter.escapeHtml(book.author);
      const stars = renderStars(book.rating);
      const href = Formatter.escapeHtml(book.link || "#");

      let coverHtml;
      if (isPlaceholderCover(book.imageUrl)) {
        coverHtml = `<div class="book-cover book-cover-fallback" style="background:${titleColor(book.title)}"><span>${escapedTitle}</span></div>`;
      } else {
        coverHtml = `<div class="book-cover"><img src="${Formatter.escapeHtml(book.imageUrl)}" alt="${escapedTitle}" loading="lazy"></div>`;
      }

      return `
    <a href="${href}" class="book-card" target="_blank" rel="noopener">
      ${coverHtml}
      <div class="book-info">
        <span class="book-title">${escapedTitle}</span>
        <span class="book-author">${escapedAuthor}</span>
        ${stars ? `<span class="book-rating">${stars}</span>` : ""}
      </div>
    </a>`;
    };

    const buildBookSection = (title, bookList) => {
      if (!bookList.length) return "";
      return `
  <section class="shelf-section">
    <h2 class="shelf-header">${title}</h2>
    <div class="shelf">
      <div class="shelf-books">${bookList.map(buildBookCard).join("")}</div>
      <div class="shelf-surface"></div>
    </div>
  </section>`;
    };

    html = TemplateRenderer.apply(html, {
      currentlyReadingSection: buildBookSection("Currently Reading", books["currently-reading"] || []),
      curatedSection: buildBookSection("Curated", curated),
      readSection: buildBookSection("Read", readBooks),
    });

    FileSystem.write(path.join(process.cwd(), "out", "bookshelf.html"), html);
  }

  buildTags(metadata, essays) {
    const tagMap = {};
    essays.forEach((essay) => {
      essay.tags.forEach((tag) => {
        if (!tagMap[tag]) tagMap[tag] = [];
        tagMap[tag].push(essay);
      });
    });

    const sortedTags = Object.entries(tagMap).sort((a, b) => b[1].length - a[1].length);

    const tagsIndexTemplate = this.dataLoader.loadTemplate("tags-index");
    const tagTemplate = this.dataLoader.loadTemplate("tag");

    let tagsIndexHtml = this.buildCommon(tagsIndexTemplate, metadata, `Tags - ${metadata.title}`, "All tags", '/tags/');
    tagsIndexHtml = TemplateRenderer.apply(tagsIndexHtml, {
      tagsCount: sortedTags.length,
      tagsList: sortedTags.map(([tag, taggedEssays]) => `
    <a href="/tags/${tag}.html" class="tag">#${Formatter.escapeHtml(tag)} <span class="count">${taggedEssays.length}</span></a>`).join(""),
    });

    FileSystem.ensureDir(path.join(process.cwd(), "out", "tags"));
    FileSystem.write(path.join(process.cwd(), "out", "tags", "index.html"), tagsIndexHtml);

    Object.entries(tagMap).forEach(([tag, taggedEssays]) => {
      let tagHtml = this.buildCommon(tagTemplate, metadata, `#${tag} - ${metadata.title}`, `Essays tagged with ${tag}`, `/tags/${tag}.html`);
      tagHtml = TemplateRenderer.apply(tagHtml, {
        tag: Formatter.escapeHtml(tag),
        taggedEssaysCount: taggedEssays.length,
        taggedEssaysCountLabel: `essay${taggedEssays.length !== 1 ? 's' : ''}`,
        taggedEssays: taggedEssays.map((post) => `
<article>
  <h2><a href="/essays/${post.slug}.html">${Formatter.escapeHtml(post.title)}</a></h2>
  <p class="meta"><time>${Formatter.formatDate(post.date)}</time></p>
  <p class="summary">${Formatter.escapeHtml(post.summary)}</p>
</article>`).join(""),
      });

      FileSystem.write(path.join(process.cwd(), "out", "tags", `${tag}.html`), tagHtml);
    });
  }
}

class SiteBuilder {
  constructor() {
    const dataDir = path.join(process.cwd(), "data", "non-public");
    this.dataLoader = new DataLoader(dataDir);
    this.markdownRenderer = new MarkdownRenderer();
    this.pageBuilder = new PageBuilder(this.dataLoader, this.markdownRenderer);
    this.outDir = path.join(process.cwd(), "out");
    this.publicDir = path.join(process.cwd(), "data", "public");
  }

  async build() {
    console.log("Reading data...");
    const metadata = this.dataLoader.readSiteMetadata();
    const author = this.dataLoader.readAuthor();
    const essays = this.dataLoader.getEssays();
    const books = this.dataLoader.getBooks();
    const projects = this.dataLoader.getProjects();
    const leetcodeSolutions = this.dataLoader.getLeetcodeSolutions();

    console.log(`Found ${essays.length} essays, ${projects.length} projects, ${leetcodeSolutions.length} leetcode solutions`);

    FileSystem.ensureDir(this.outDir);
    FileSystem.clearDir(this.outDir);
    FileSystem.copyDir(this.publicDir, this.outDir);

    console.log("Building pages...");
    const avatar = `${process.env.BASE_PATH || ''}/static/images/avatar.jpg`;
    await this.pageBuilder.buildHome(metadata, essays, books, projects, author, avatar);
    await this.pageBuilder.buildEssaysList(metadata, essays);
    for (const essay of essays) {
      await this.pageBuilder.buildEssay(metadata, essay);
    }
    this.pageBuilder.buildTags(metadata, essays);
    await this.pageBuilder.buildAbout(metadata, author, avatar);
    this.pageBuilder.buildProjects(metadata, projects);
    this.pageBuilder.buildBookshelf(metadata, books);

    console.log("Generating RSS, sitemap, and robots.txt...");
    FileSystem.write(path.join(this.outDir, "feed.xml"), FeedGenerator.generateRssFeed(metadata, essays));
    FileSystem.write(path.join(this.outDir, "sitemap.xml"), FeedGenerator.generateSitemap(metadata, essays, projects, leetcodeSolutions));
    FileSystem.write(path.join(this.outDir, "robots.txt"), `User-agent: *\nAllow: /\n\nSitemap: ${metadata.siteUrl}sitemap.xml`);

    console.log("Done! Static site generated in out/");
  }
}

new SiteBuilder().build();
