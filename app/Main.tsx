import Link from '@/components/Link'
import Image from '@/components/Image'
import siteMetadata from '@/data/siteMetadata'
import { formatDate } from 'pliny/utils/formatDate'
import { allAuthors, Authors } from 'contentlayer/generated'
import { coreContent } from 'pliny/utils/contentlayer'
import { MDXLayoutRenderer } from 'pliny/mdx-components'
import Bookshelf from '@/components/books'
import SampleProjects from '@/components/SampleProjects'
import { BlogPosting, WithContext } from 'schema-dts'

const MAX_DISPLAY = 10

export default function Home({ posts, books, projects }) {
  const author = allAuthors.find((p) => p.slug === 'default') as Authors
  const mainContent = coreContent(author)

  const structuredData: WithContext<BlogPosting>[] = posts.slice(0, MAX_DISPLAY).map((post) => ({
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    datePublished: post.date,
    description: post.summary,
    author: {
      '@type': 'Person',
      name: siteMetadata.author,
    },
    url: `${siteMetadata.siteUrl}/essays/${post.slug}`,
  }))

  return (
    <>
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-8 lg:flex-row">
          {/* Main Content (News Feed style) */}
          <div className="w-full lg:w-3/4">
            <div className="card-simple mb-6">
              <div className="mb-4 border-b border-gray-200 pb-2 dark:border-gray-700">
                <h2 className="text-lg font-bold text-primary-500">Latest Essays</h2>
              </div>

              <div className="space-y-6">
                {!posts.length && <p className="text-gray-500">No posts found.</p>}
                {posts.slice(0, MAX_DISPLAY).map((post) => {
                  const { slug, date, title, summary, tags } = post
                  return (
                    <article
                      key={slug}
                      className="flex flex-col gap-2 border-b border-gray-100 pb-6 last:border-0 dark:border-gray-800"
                    >
                      <div className="flex items-baseline justify-between">
                        <h3 className="text-2xl font-bold text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300">
                          <Link href={`/essays/${slug}`}>{title}</Link>
                        </h3>
                        <time
                          dateTime={date}
                          className="shrink-0 text-base text-gray-500 dark:text-gray-400"
                        >
                          {formatDate(date, siteMetadata.locale)}
                        </time>
                      </div>
                      <div className="prose max-w-none text-gray-600 dark:text-gray-300">
                        {summary}
                      </div>
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/essays/${slug}`}
                          className="text-base font-bold text-gray-500 hover:underline dark:text-gray-400"
                        >
                          Read more &rarr;
                        </Link>
                        {tags && tags.length > 0 && (
                          <div className="flex gap-1">
                            {tags.slice(0, 3).map((tag) => (
                              <span key={tag} className="text-sm text-secondary-500">
                                #{tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </article>
                  )
                })}
              </div>
              {posts.length > MAX_DISPLAY && (
                <div className="mt-6 flex justify-end">
                  <Link
                    href="/essays"
                    className="text-base font-medium text-primary-600 hover:text-primary-800 dark:text-primary-400"
                  >
                    View Archive &rarr;
                  </Link>
                </div>
              )}
            </div>

            {/* Featured Projects (shown in main column lower down) */}
            <div className="card-simple mb-6">
              <div className="mb-4 border-b border-gray-200 pb-2 dark:border-gray-700">
                <h2 className="text-lg font-bold text-primary-500">Featured Projects</h2>
              </div>
              <SampleProjects projects={projects.slice(0, 4)} />
            </div>
          </div>

          {/* Sidebar */}
          <div className="w-full space-y-6 lg:w-1/4">
            {/* Author / Profile */}
            <div className="card-simple">
              <div className="flex flex-col items-center pb-4">
                {author.avatar && (
                  <Image
                    src={author.avatar}
                    alt="avatar"
                    width={120}
                    height={120}
                    className="h-32 w-32 rounded-full border-4 border-white shadow-lg dark:border-gray-800"
                  />
                )}
              </div>
              <div className="mb-4 border-b border-gray-200 pb-2 dark:border-gray-700">
                <h3 className="text-sm font-bold text-gray-700 dark:text-gray-200">
                  About {siteMetadata.author}
                </h3>
              </div>
              <div className="prose dark:prose-invert">
                <p>
                  {author.body.raw.split('\n\n')[0]} ...
                  <Link href="/about">read more</Link>
                </p>
              </div>
            </div>

            {/* Reading List Widget */}
            <div className="card-simple">
              <div className="mb-4 border-b border-gray-200 pb-2 dark:border-gray-700">
                <h3 className="text-sm font-bold text-gray-700 dark:text-gray-200">Reading List</h3>
              </div>
              <ul className="list-none space-y-2 pl-0">
                {books.slice(0, 5).map((book) => (
                  <li key={book.link} className="pl-0">
                    <a
                      href={book.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group flex w-full items-center justify-between text-gray-600 transition-colors hover:text-primary-500 dark:text-gray-300"
                    >
                      <span className="truncate">{book.title}</span>
                      <span className="ml-2 shrink-0 text-xs text-gray-400 group-hover:text-primary-400">
                        ↗
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
    </>
  )
}
