import { Metadata } from 'next'
import booksData from '@/data/books.json'
import Image from 'next/image'
import BookCard from '@/components/BookCard'

export const metadata: Metadata = {
  title: 'Bookshelf',
  description: 'Books I am reading and have read.',
}

import { getBooks, Book } from '@/lib/data'

export default async function BookshelfPage() {
  const currentlyReading = await getBooks('currently-reading')
  const read = await getBooks('read')

  return (
    <div className="divide-y divide-gray-200 dark:divide-gray-700">
      <div className="space-y-2 pb-8 pt-6 md:space-y-5">
        <h1 className="text-3xl font-extrabold leading-9 tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14">
          Bookshelf
        </h1>
        <p className="text-lg leading-7 text-gray-500 dark:text-gray-400">
          A collection of books I'm currently reading and have read.
        </p>
      </div>

      <div className="container py-12">
        <div className="space-y-12">
          {currentlyReading.length > 0 && (
            <section>
              <h2 className="mb-8 text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
                Currently Reading
              </h2>
              <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
                {currentlyReading.map((book) => (
                  <BookCard key={book.link} book={book} />
                ))}
              </div>
            </section>
          )}

          <section>
            <h2 className="mb-8 text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
              Read
            </h2>
            <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {read.map((book) => (
                <BookCard key={book.link} book={book} />
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
