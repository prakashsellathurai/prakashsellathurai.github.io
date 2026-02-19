import { Metadata } from 'next'
import booksData from '@/data/books.json'
import Image from 'next/image'
import BookCard from '@/components/BookCard'

export const metadata: Metadata = {
  title: 'Bookshelf',
  description: 'Books I am reading and have read.',
}

import { getBooks, Book } from '@/lib/data'
import { generateCollectionPageSchema, generateItemListSchema } from '@/lib/generateStructuredData'

export default async function BookshelfPage() {
  const currentlyReading = await getBooks('currently-reading')
  const read = await getBooks('read')

  const bookshelfSchema = generateCollectionPageSchema('bookshelf')
  const currentlyReadingSchema =
    currentlyReading.length > 0
      ? generateItemListSchema(currentlyReading, 'Currently Reading')
      : null
  const readSchema = read.length > 0 ? generateItemListSchema(read, 'Books I Have Read') : null

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(bookshelfSchema) }}
      />
      {currentlyReadingSchema && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(currentlyReadingSchema) }}
        />
      )}
      {readSchema && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(readSchema) }}
        />
      )}
      <div className="divide-y divide-black/10 dark:divide-white/10">
        {/* Enhanced Header */}
        <div className="space-y-2 pb-8 pt-6 md:space-y-5">
          <h1 className="bg-gradient-to-r from-black via-primary-600 to-secondary-600 bg-clip-text text-3xl font-extrabold leading-9 tracking-tight text-transparent dark:from-white dark:via-primary-400 dark:to-secondary-400 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14">
            Bookshelf
          </h1>
          <p className="text-lg leading-7 text-black dark:text-white">
            A collection of books I'm currently reading and have read.
          </p>
        </div>

        <div className="container py-12">
          <div className="glass-panel-enhanced space-y-12 rounded-3xl p-8 md:p-10">
            {currentlyReading.length > 0 && (
              <section>
                <div className="mb-8 flex items-center gap-4">
                  <div className="h-1 w-12 rounded-full bg-gradient-to-r from-secondary-500 to-primary-500" />
                  <h2 className="text-2xl font-bold tracking-tight text-black dark:text-white">
                    Currently Reading
                  </h2>
                </div>
                <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
                  {currentlyReading.map((book) => (
                    <BookCard key={book.link} book={book} />
                  ))}
                </div>
              </section>
            )}

            <section>
              <div className="mb-8 flex items-center gap-4">
                <div className="h-1 w-12 rounded-full bg-gradient-to-r from-primary-500 to-secondary-500" />
                <h2 className="text-2xl font-bold tracking-tight text-black dark:text-white">
                  Read
                </h2>
              </div>
              <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
                {read.map((book) => (
                  <BookCard key={book.link} book={book} />
                ))}
              </div>
            </section>
          </div>
        </div>
      </div>
    </>
  )
}
