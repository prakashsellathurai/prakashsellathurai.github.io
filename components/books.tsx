import React from 'react'
import Image from './Image'
import { Book } from '@/lib/data'

const Bookshelf: React.FC<{ books: Book[] }> = ({ books }) => {
  return (
    <div>
      <h2 className="mb-6 text-3xl font-bold">
        {' '}
        <a href="/bookshelf">Bookshelf</a>
      </h2>
      <div className="bg-gray-100 p-6 dark:bg-gray-800">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3">
          {books.map((book, index) => (
            <a key={book.title} href={book.link} target="_blank" rel="noopener noreferrer">
              <div
                key={index}
                className="flex h-96 flex-col rounded-lg bg-white p-4 shadow-md dark:bg-gray-900"
              >
                <Image
                  src={book.imageUrl}
                  alt={book.title}
                  width={200}
                  height={200}
                  className="mb-4 h-64 w-full rounded-md object-contain"
                />
                <p className="text-l font-semibold">{book.title}</p>
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Bookshelf
