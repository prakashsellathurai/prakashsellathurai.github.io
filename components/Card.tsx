import Image from './Image'
import Link from './Link'
import { Project } from '@/data/projectsData'

type CardProps = Project

const Card = ({
  title,
  description,
  imgSrc,
  href,
  stars,
  language,
  forks,
  tags,
  updatedAt,
}: CardProps) => {
  // Format the date to show relative time
  const getRelativeTime = (dateString?: string) => {
    if (!dateString) return null
    const date = new Date(dateString)
    const now = new Date()
    const diffInMs = now.getTime() - date.getTime()
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))

    if (diffInDays === 0) return 'Updated today'
    if (diffInDays === 1) return 'Updated yesterday'
    if (diffInDays < 30) return `Updated ${diffInDays}d ago`
    if (diffInDays < 365) return `Updated ${Math.floor(diffInDays / 30)}mo ago`
    return `Updated ${Math.floor(diffInDays / 365)}y ago`
  }

  // Get language color (common GitHub language colors)
  const getLanguageColor = (lang?: string) => {
    const colors: { [key: string]: string } = {
      JavaScript: '#f1e05a',
      TypeScript: '#3178c6',
      Python: '#3572A5',
      Java: '#b07219',
      Go: '#00ADD8',
      Rust: '#dea584',
      Ruby: '#701516',
      PHP: '#4F5D95',
      'C++': '#f34b7d',
      C: '#555555',
      HTML: '#e34c26',
      CSS: '#563d7c',
      Shell: '#89e051',
      Jupyter: '#DA5B0B',
    }
    return colors[lang || ''] || '#8b8b8b'
  }

  return (
    <div className="card-project animate-diagonal-open group relative size-full overflow-hidden rounded-3xl border border-black/10 bg-white/20 backdrop-blur-xl transition-all duration-500 hover:scale-[1.02] hover:border-black/20 hover:shadow-xl dark:border-white/10 dark:bg-black/20">
      {/* Hover glow effect - Neutral Primary */}
      <div className="pointer-events-none absolute inset-0 rounded-3xl opacity-0 transition-opacity duration-500 group-hover:opacity-100">
        <div className="absolute inset-0 rounded-3xl bg-primary-500/5" />
      </div>

      {/* Image Section */}
      {imgSrc && (
        <div className="relative overflow-hidden">
          {href ? (
            <Link href={href} aria-label={`Link to ${title}`}>
              <Image
                alt={title}
                src={imgSrc}
                className="object-cover object-center transition-transform duration-500 group-hover:scale-110 md:h-36 lg:h-48"
                width={544}
                height={306}
              />
            </Link>
          ) : (
            <Image
              alt={title}
              src={imgSrc}
              className="object-cover object-center transition-transform duration-500 group-hover:scale-110 md:h-36 lg:h-48"
              width={544}
              height={306}
            />
          )}
          {/* Gradient overlay on image */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
        </div>
      )}

      {/* Content Section */}
      <div className="relative p-6">
        {/* Title */}
        <h2 className="mb-3 text-2xl font-bold leading-8 tracking-tight transition-colors duration-300 group-hover:text-primary-600 dark:group-hover:text-primary-400">
          {href ? (
            <Link href={href} aria-label={`Link to ${title}`} className="hover:underline">
              {title}
            </Link>
          ) : (
            title
          )}
        </h2>

        {/* Description */}
        <p className="prose mb-4 line-clamp-3 max-w-none text-gray-600 dark:text-gray-400">
          {description || 'No description available'}
        </p>

        {/* Metadata Row */}
        <div className="mb-4 flex flex-wrap items-center gap-3 text-sm">
          {/* Stars */}
          {stars !== undefined && stars > 0 && (
            <div className="flex items-center gap-1 text-yellow-600 dark:text-yellow-500">
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              <span className="font-semibold">{stars}</span>
            </div>
          )}

          {/* Forks */}
          {forks !== undefined && forks > 0 && (
            <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 16 16">
                <path
                  fillRule="evenodd"
                  d="M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z"
                />
              </svg>
              <span>{forks}</span>
            </div>
          )}

          {/* Language */}
          {language && (
            <div className="flex items-center gap-1.5">
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: getLanguageColor(language) }}
              />
              <span className="text-gray-700 dark:text-gray-300">{language}</span>
            </div>
          )}

          {/* Updated time */}
          {updatedAt && (
            <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="text-xs">{getRelativeTime(updatedAt)}</span>
            </div>
          )}
        </div>

        {/* Tags */}
        {tags && tags.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-2">
            {tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-primary-100 px-3 py-1 text-xs font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-300"
              >
                {tag}
              </span>
            ))}
            {tags.length > 3 && (
              <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                +{tags.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Learn More Link */}
        {href && (
          <Link
            href={href}
            className="group/link inline-flex items-center gap-1 text-base font-medium leading-6 text-gray-900 transition-all duration-300 hover:gap-2 hover:text-primary-600 dark:text-gray-100 dark:hover:text-primary-400"
            aria-label={`Link to ${title}`}
          >
            Learn more
            <svg
              className="h-4 w-4 transition-transform duration-300 group-hover/link:translate-x-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 8l4 4m0 0l-4 4m4-4H3"
              />
            </svg>
          </Link>
        )}
      </div>

      {/* Blueprint-style corner brackets - Neutral Secondary */}
      <div className="pointer-events-none absolute left-2 top-2 h-4 w-4 border-l border-t border-primary-400/20 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      <div className="pointer-events-none absolute bottom-2 right-2 h-4 w-4 border-b border-r border-primary-400/20 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
    </div>
  )
}

export default Card
