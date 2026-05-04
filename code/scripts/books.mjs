import fs from 'fs'

const SHELVES = ['currently-reading', 'read', 'curated']

async function getBooks(shelf) {
  const url = `https://www.goodreads.com/review/list_rss/105903487?shelf=${shelf}`
  try {
    const res = await fetch(url)
    if (!res.ok) {
      throw new Error(`Failed to fetch books for shelf ${shelf}`)
    }
    const xml = await res.text()
    return parseBooks(xml)
  } catch (error) {
    console.error(error)
    return []
  }
}

function parseBooks(xml) {
  const books = []
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

async function fetchBooks() {
  const booksData = {}
  for (const shelf of SHELVES) {
    console.log(`Fetching books for shelf: ${shelf}`)
    booksData[shelf] = await getBooks(shelf)
  }

  fs.writeFileSync('./data/books.json', JSON.stringify(booksData, null, 2), 'utf-8')
  console.log('Books data saved to ./data/books.json')
}

fetchBooks()
