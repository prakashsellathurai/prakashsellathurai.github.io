import siteMetadata from '@/data/siteMetadata'
import { Essay } from 'contentlayer/generated'
import { Book } from '@/lib/data'

/**
 * Generate Person schema for the website author
 */
export function generatePersonSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Person',
    ...siteMetadata.authorDetails,
  }
}

/**
 * Generate WebSite schema with sitelinks search box
 */
export function generateWebSiteSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: siteMetadata.title,
    description: siteMetadata.description,
    url: siteMetadata.siteUrl,
    inLanguage: siteMetadata.language,
    author: {
      '@type': 'Person',
      name: siteMetadata.author,
      url: siteMetadata.siteUrl,
    },
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${siteMetadata.siteUrl}/search?q={search_term_string}`,
      },
      'query-input': 'required name=search_term_string',
    },
  }
}

/**
 * Generate enhanced Article schema for blog posts
 */
export function generateArticleSchema(
  post: Essay,
  authorName: string,
  authorUrl?: string,
  images?: string[]
) {
  const publishedDate = new Date(post.date).toISOString()
  const modifiedDate = new Date(post.lastmod || post.date).toISOString()
  const imageList = images || [siteMetadata.socialBanner]

  return {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: post.title,
    description: post.summary,
    image: imageList,
    datePublished: publishedDate,
    dateModified: modifiedDate,
    author: {
      '@type': 'Person',
      name: authorName,
      url: authorUrl || siteMetadata.siteUrl,
    },
    publisher: {
      '@type': 'Person',
      name: siteMetadata.author,
    },
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': `${siteMetadata.siteUrl}/essays/${post.slug}`,
    },
    inLanguage: siteMetadata.language,
    ...(post.tags && { keywords: post.tags.join(', ') }),
  }
}

/**
 * Generate BreadcrumbList schema for navigation
 */
export function generateBreadcrumbSchema(items: { name: string; url: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url,
    })),
  }
}

/**
 * Generate Blog schema for essays list page
 */
export function generateBlogSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Blog',
    name: `${siteMetadata.title} - Essays`,
    description:
      'Technical essays and thoughts on software engineering, web development, and technology',
    url: `${siteMetadata.siteUrl}/essays`,
    author: {
      '@type': 'Person',
      name: siteMetadata.author,
      url: siteMetadata.siteUrl,
    },
    inLanguage: siteMetadata.language,
  }
}

/**
 * Generate ProfilePage schema for about page
 */
export function generateProfilePageSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'ProfilePage',
    mainEntity: siteMetadata.authorDetails,
    name: `About ${siteMetadata.author}`,
    description: siteMetadata.description,
    url: `${siteMetadata.siteUrl}/about`,
  }
}

/**
 * Generate CollectionPage schema for projects
 */
export function generateCollectionPageSchema(pageType: 'projects' | 'bookshelf') {
  const titles = {
    projects: 'Projects',
    bookshelf: 'Bookshelf',
  }

  const descriptions = {
    projects: 'Showcase of open-source projects and technical work',
    bookshelf: 'Collection of books and reading recommendations',
  }

  return {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: `${siteMetadata.title} - ${titles[pageType]}`,
    description: descriptions[pageType],
    url: `${siteMetadata.siteUrl}/${pageType}`,
    author: {
      '@type': 'Person',
      name: siteMetadata.author,
      url: siteMetadata.siteUrl,
    },
  }
}

/**
 * Generate Book schema for a specific book
 */
export function generateBookSchema(book: Book) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Book',
    name: book.title,
    author: {
      '@type': 'Person',
      name: book.author,
    },
    image: book.imageUrl,
    url: book.link,
    ...(book.description && { description: book.description }),
  }
}

/**
 * Generate ItemList schema for a collection of books
 */
export function generateItemListSchema(books: Book[], listName: string) {
  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: listName,
    itemListElement: books.map((book, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      item: generateBookSchema(book),
    })),
  }
}
