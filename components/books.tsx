import React from 'react'
import Image from './Image'
import BookCard from './BookCard'
import { Book } from '@/lib/data'

const Bookshelf: React.FC<{ books: Book[] }> = ({ books }) => {
  return (
    <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      {books.map((book) => (
        <BookCard key={book.link} book={book} />
      ))}
    </div>
  )
}

export default Bookshelf
