import booksData from '@/data/books.json'
import {
  projectsData as fallbackProjectsData,
  Project,
  projectsNamesToShowcase,
} from '@/data/projectsData'

export interface Book {
  title: string
  link: string
  imageUrl: string
  author: string
  rating?: string
  description?: string
  pubDate?: string
}

export async function getBooks(shelf: string): Promise<Book[]> {
  const url = `https://www.goodreads.com/review/list_rss/105903487?shelf=${shelf}`
  try {
    const res = await fetch(url, { next: { revalidate: 3600 } })
    if (!res.ok) {
      throw new Error(`Failed to fetch books for shelf ${shelf}`)
    }
    const xml = await res.text()
    return parseBooks(xml)
  } catch (error) {
    console.error(error)
    // @ts-ignore
    const fallback = booksData[shelf]
    if (!fallback && shelf === 'curated') {
      // @ts-ignore
      return booksData['read']?.filter((b) => b.rating === '5') || []
    }
    return fallback || []
  }
}

function parseBooks(xml: string): Book[] {
  const books: Book[] = []
  const itemRegex = /<item>([\s\S]*?)<\/item>/g
  let match

  while ((match = itemRegex.exec(xml)) !== null) {
    const itemContent = match[1]

    const titleMatch = itemContent.match(/<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/)
    const linkMatch = itemContent.match(/<link>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/link>/)
    const imageMatch =
      itemContent.match(
        /<book_large_image_url>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/book_large_image_url>/
      ) ||
      itemContent.match(/<book_image_url>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/book_image_url>/)
    const authorMatch = itemContent.match(
      /<author_name>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/author_name>/
    )
    const ratingMatch = itemContent.match(
      /<user_rating>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/user_rating>/
    )
    const descriptionMatch = itemContent.match(
      /<book_description>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/book_description>/
    )
    const pubDateMatch = itemContent.match(
      /<pubDate>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/pubDate>/
    )

    if (titleMatch && linkMatch && imageMatch && authorMatch) {
      books.push({
        title: titleMatch[1].trim(),
        link: linkMatch[1].trim(),
        imageUrl: imageMatch[1].trim(),
        author: authorMatch[1].trim(),
        rating: ratingMatch ? ratingMatch[1].trim() : undefined,
        description: descriptionMatch
          ? descriptionMatch[1].replace(/<[^>]*>?/gm, '').trim()
          : undefined, // Strip HTML from description
        pubDate: pubDateMatch ? pubDateMatch[1].trim() : undefined,
      })
    }
  }
  return books
}

export async function getProjects(): Promise<Project[]> {
  try {
    const res = await fetch('https://api.github.com/users/prakashsellathurai/repos?per_page=100', {
      next: { revalidate: 3600 },
    })

    if (!res.ok) {
      throw new Error('Failed to fetch projects')
    }

    const repos = await res.json()
    const allProjects = repos.map((repo) => ({
      title: repo.name,
      description: repo.description,
      href: repo.html_url,
      imgSrc: undefined, // GitHub API doesn't provide image, fallback or handle elsewhere?
      stars: repo.stargazers_count,
    }))

    return allProjects.filter((project) => projectsNamesToShowcase.includes(project.title))
  } catch (error) {
    console.error('Error fetching projects:', error)
    return fallbackProjectsData.filter((project) => projectsNamesToShowcase.includes(project.title))
  }
}
