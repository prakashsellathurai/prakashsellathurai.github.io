import Image from './Image'
import Link from './Link'
import { Book } from '@/lib/data'

const BookCard = ({ book }: { book: Book }) => {
  return (
    <a
      href={book.link}
      target="_blank"
      rel="noopener noreferrer"
      className="animate-diagonal-open group relative flex flex-col overflow-hidden rounded-2xl border border-black/10 bg-white/80 backdrop-blur-md transition-all duration-300 hover:scale-[1.02] hover:border-primary-400/60 hover:shadow-xl dark:border-white/10 dark:bg-white/5"
    >
      <div className="relative aspect-[2/3] w-full overflow-hidden bg-black/5 dark:bg-white/5">
        <Image
          src={book.imageUrl}
          alt={book.title}
          fill
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          className="object-cover object-center transition-transform duration-500 group-hover:scale-110"
        />
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      </div>
      <div className="flex flex-1 flex-col p-5">
        <h3 className="mb-2 text-lg font-bold leading-tight text-black transition-colors duration-300 group-hover:text-primary-600 dark:text-white dark:group-hover:text-primary-400">
          {book.title}
        </h3>
        <p className="mb-3 text-sm font-medium text-black dark:text-white">{book.author}</p>

        {book.rating && parseInt(book.rating) > 0 && (
          <div className="mt-auto flex items-center gap-1 text-yellow-500">
            {[...Array(5)].map((_, i) => (
              <svg
                key={i}
                className={`h-4 w-4 ${i < parseInt(book.rating!) ? 'fill-current' : 'text-black dark:text-white'}`}
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

export default BookCard
