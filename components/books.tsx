import React from 'react'
import Image from './Image'
const books = [
  {
    title: 'Warnings: Finding Cassandras to Stop Catastrophes',
    cover:
      'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1495550719l/32600755._SX500_.jpg',
    link: 'https://www.goodreads.com/book/show/32600755-warnings',
  },
  {
    title:
      'The Art of the Start: The Time-Tested, Battle-Hardened Guide for Anyone Starting Anything',
    cover:
      'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1433719169l/37875._SX500_.jpg',
    link: 'https://www.goodreads.com/book/show/37875.The_Art_of_the_Start',
  },
  {
    title: 'Never Split the Difference: Negotiating as if Your Life Depended on It',
    cover:
      'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1680014152l/123857637._SX500_.jpg',
    link: 'https://www.goodreads.com/book/show/123857637-never-split-the-difference',
  },
  {
    title: 'Hackers & Painters: Big Ideas from the Computer Age',
    cover:
      'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1387653624i/6565257._SX500_.jpg',
    link: 'https://www.goodreads.com/book/show/6565257-hackers-painters',
  },
  {
    title: 'The Return of the King (The Lord of the Rings, #3)',
    cover:
      'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1654216226l/61215384._SX500_.jpg',
    link: 'https://www.goodreads.com/book/show/61215384-the-return-of-the-king',
  },
  {
    title: 'Memoirs of European Travel',
    cover:
      'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1561342203l/1343607._SX500_.jpg',
    link: 'https://www.goodreads.com/book/show/1343607.Memoirs_of_European_Travel',
  },
  {
    title: 'Zero to One: Notes on Startups, or How to Build the Future',
    cover:
      'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1630663027l/18050143._SX500_.jpg',
    link: 'https://www.goodreads.com/book/show/18050143-zero-to-one',
  },
  {
    title: 'The Art of War',
    cover:
      'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1551957016l/44297006._SX500_.jpg',
    link: 'https://www.goodreads.com/book/show/44297006-the-art-of-war',
  },
  {
    title: 'The Two Towers (The Lord of the Rings, #2)',
    cover:
      'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1486871714l/222910._SX500_.jpg',
    link: 'https://www.goodreads.com/book/show/222910.The_Two_Towers',
  },
]

const Bookshelf: React.FC = () => {
  return (
    <div>
      <h2 className="mb-6 text-3xl font-bold">
        {' '}
        <a href="https://www.goodreads.com/user/show/105903487-prakash-sellathurai">Bookshelf</a>
      </h2>
      <div className="bg-gray-100 p-6">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3">
          {books.map((book, index) => (
            <a key={book.title} href={book.link} target="_blank" rel="noopener noreferrer">
              <div key={index} className="flex h-96 flex-col rounded-lg bg-white p-4 shadow-md">
                <Image
                  src={book.cover}
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
