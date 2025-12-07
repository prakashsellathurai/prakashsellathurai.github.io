import { Metadata } from 'next'
import booksData from '@/data/books.json'
import Image from 'next/image'

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

function BookCard({ book }: { book: Book }) {
  return (
    <a
      href={book.link}
      target="_blank"
      rel="noopener noreferrer"
      className="group relative flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-all hover:shadow-md dark:border-gray-800 dark:bg-gray-900"
    >
      <div className="relative aspect-[2/3] w-full overflow-hidden bg-gray-100 dark:bg-gray-800">
        <Image
          src={book.imageUrl}
          alt={book.title}
          fill
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          className="object-cover object-center transition-transform duration-300 group-hover:scale-105"
        />
      </div>
      <div className="flex flex-1 flex-col p-4">
        <h3 className="mb-1 text-lg font-bold leading-tight text-gray-900 group-hover:text-primary-500 dark:text-gray-100 dark:group-hover:text-primary-400">
          {book.title}
        </h3>
        <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">{book.author}</p>
        {book.rating && parseInt(book.rating) > 0 && (
          <div className="mt-auto flex items-center text-yellow-400">
            {[...Array(5)].map((_, i) => (
              <svg
                key={i}
                className={`h-4 w-4 ${i < parseInt(book.rating!) ? 'fill-current' : 'text-gray-300 dark:text-gray-600'}`}
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ))}
          </div>
        )}
      </div>
    </a>
  )
}
