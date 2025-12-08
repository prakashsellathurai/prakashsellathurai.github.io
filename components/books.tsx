import React from 'react'
import Image from './Image'
import BookCard from './BookCard'
import { Book } from '@/lib/data'

const Bookshelf: React.FC<{ books: Book[] }> = ({ books }) => {
  return (
    <div>
      <h2 className="mb-6 text-3xl font-bold">
        {' '}
        <a href="/bookshelf">Bookshelf</a>
      </h2>
      <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
        {books.map((book) => (
          <BookCard key={book.link} book={book} />
        ))}
      </div>
    </div>
  )
}

export default Bookshelf
