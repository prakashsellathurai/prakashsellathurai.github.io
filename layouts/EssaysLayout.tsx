'use client'

import { usePathname } from 'next/navigation'
import { slug } from 'github-slugger'
import { formatDate } from 'pliny/utils/formatDate'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Essay } from 'contentlayer/generated'
import Link from '@/components/Link'
import Tag from '@/components/Tag'
import siteMetadata from '@/data/siteMetadata'
import tagData from 'app/tag-data.json'

interface PaginationProps {
  totalPages: number
  currentPage: number
}
interface ListLayoutProps {
  posts: CoreContent<Essay>[]
  title: string
  initialDisplayPosts?: CoreContent<Essay>[]
  pagination?: PaginationProps
}

function Pagination({ totalPages, currentPage }: PaginationProps) {
  const pathname = usePathname()
  const segments = pathname.split('/')
  const lastSegment = segments[segments.length - 1]
  const basePath = pathname
    .replace(/^\//, '') // Remove leading slash
    .replace(/\/page\/\d+$/, '') // Remove any trailing /page
  const prevPage = currentPage - 1 > 0
  const nextPage = currentPage + 1 <= totalPages

  return (
    <div className="space-y-2 pb-8 pt-6 md:space-y-5">
      <nav className="flex justify-between">
        {!prevPage && (
          <button className="cursor-auto disabled:opacity-50" disabled={!prevPage}>
            Previous
          </button>
        )}
        {prevPage && (
          <Link
            href={currentPage - 1 === 1 ? `/${basePath}/` : `/${basePath}/page/${currentPage - 1}`}
            rel="prev"
          >
            Previous
          </Link>
        )}
        <span>
          {currentPage} of {totalPages}
        </span>
        {!nextPage && (
          <button className="cursor-auto disabled:opacity-50" disabled={!nextPage}>
            Next
          </button>
        )}
        {nextPage && (
          <Link href={`/${basePath}/page/${currentPage + 1}`} rel="next">
            Next
          </Link>
        )}
      </nav>
    </div>
  )
}

export default function EssaysLayout({
  posts,
  title,
  initialDisplayPosts = [],
  pagination,
}: ListLayoutProps) {
  const pathname = usePathname()
  const tagCounts = tagData as Record<string, number>
  const tagKeys = Object.keys(tagCounts)
  const sortedTags = tagKeys.sort((a, b) => tagCounts[b] - tagCounts[a])

  const displayPosts = initialDisplayPosts.length > 0 ? initialDisplayPosts : posts

  return (
    <>
      <div className="pb-6 pt-6">
        <h1 className="bg-gradient-to-r from-black via-primary-600 to-secondary-600 bg-clip-text text-3xl font-extrabold leading-9 tracking-tight text-transparent dark:from-white dark:via-primary-400 dark:to-secondary-400 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14">
          {title}
        </h1>
      </div>

      <div className="flex flex-col sm:flex-row sm:space-x-8 lg:space-x-12">
        {/* Sidebar - Modern Glass Style */}
        <div className="glass-panel-enhanced animate-diagonal-open mb-8 hidden h-max min-w-[280px] max-w-[280px] flex-none rounded-2xl border-black/20 p-6 shadow-lg sm:mb-0 sm:flex">
          <div className="w-full">
            <h3 className="mb-4 font-bold uppercase tracking-wider text-primary-500">Category</h3>
            <div className="mb-6 h-px w-full bg-gradient-to-r from-primary-500/50 to-transparent" />

            <ul>
              <li className="my-2">
                {pathname.startsWith('/blog') || pathname === '/essays' ? (
                  <span className="flex items-center justify-between rounded-lg bg-primary-500/10 px-3 py-2 text-sm font-bold text-primary-500 transition-all">
                    <span>All Essays</span>
                    <span className="rounded-full bg-primary-100 px-2 py-0.5 text-xs dark:bg-primary-900/30">
                      {posts.length}
                    </span>
                  </span>
                ) : (
                  <Link
                    href={`/essays`}
                    className="flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium text-black transition-all hover:bg-black/5 dark:text-white dark:hover:bg-white/5"
                  >
                    <span>All Essays</span>
                  </Link>
                )}
              </li>

              {sortedTags.map((t) => {
                const isSelected = decodeURI(pathname.split('/tags/')[1]) === slug(t)
                return (
                  <li key={t} className="my-1">
                    {isSelected ? (
                      <span className="flex items-center justify-between rounded-lg bg-primary-500/10 px-3 py-2 text-sm font-bold text-primary-500 transition-all">
                        <span>{t}</span>
                        <span className="rounded-full bg-primary-100 px-2 py-0.5 text-xs dark:bg-primary-900/30">
                          {tagCounts[t]}
                        </span>
                      </span>
                    ) : (
                      <Link
                        href={`/tags/${slug(t)}`}
                        className="flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium text-black transition-all hover:translate-x-1 hover:bg-black/5 dark:text-white dark:hover:bg-white/5"
                        aria-label={`View posts tagged ${t}`}
                      >
                        <span>{t}</span>
                        <span className="text-xs text-black dark:text-white">{tagCounts[t]}</span>
                      </Link>
                    )}
                  </li>
                )
              })}
            </ul>
          </div>
        </div>

        {/* Main Content - Mixed Modern & Old */}
        <div className="min-w-0 flex-1">
          <ul className="space-y-8">
            {displayPosts.map((post, index) => {
              const { path, date, title, summary, tags } = post
              return (
                <li
                  key={path}
                  className="glass-panel-enhanced animate-diagonal-open group relative overflow-hidden rounded-2xl border border-black/20 p-6 transition-all duration-300 "
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  {/* Blueprint/Tech Decor - The "Old" Aspect */}
                  <div className="absolute right-0 top-0 p-3 opacity-30 transition-opacity group-hover:opacity-100">
                    <div className="flex gap-1">
                      <div className="h-1 w-1 rounded-full bg-primary-500"></div>
                      <div className="h-1 w-1 rounded-full bg-primary-500"></div>
                      <div className="h-1 w-1 rounded-full bg-primary-500"></div>
                    </div>
                  </div>

                  {/* Corner accents */}
                  <div className="absolute left-0 top-0 h-8 w-8 rounded-tl-xl border-l-2 border-t-2 border-primary-500/0 transition-all duration-500 group-hover:border-primary-500/30"></div>
                  <div className="absolute bottom-0 right-0 h-8 w-8 rounded-br-xl border-b-2 border-r-2 border-primary-500/0 transition-all duration-500 group-hover:border-primary-500/30"></div>

                  <article className="flex flex-col space-y-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <dl>
                          <dt className="sr-only">Published on</dt>
                          <dd className="flex items-center gap-2 text-sm font-medium leading-6 text-black dark:text-white">
                            <span className="h-2 w-2 animate-pulse rounded-full bg-primary-500"></span>
                            <time dateTime={date} suppressHydrationWarning className="font-mono">
                              {formatDate(date, siteMetadata.locale)}
                            </time>
                          </dd>
                        </dl>
                      </div>

                      <h2 className="text-2xl font-bold leading-8 tracking-tight">
                        <Link
                          href={`/${path}`}
                          className="text-black transition-colors group-hover:text-primary-600 dark:text-white dark:group-hover:text-primary-400"
                        >
                          {title}
                        </Link>
                      </h2>

                      <div className="flex flex-wrap gap-2">
                        {tags?.map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center rounded-md bg-primary-50 px-2 py-1 text-xs font-medium text-primary-700 ring-1 ring-inset ring-primary-700/10 dark:bg-primary-900/20 dark:text-primary-300"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="prose max-w-none border-l-2 border-primary-500/20 pl-4 text-black dark:text-white">
                      {summary}
                    </div>

                    <div className="pt-2">
                      <Link
                        href={`/${path}`}
                        className="group/link inline-flex items-center gap-2 text-sm font-semibold text-primary-600 transition-all hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                        aria-label={`Read "${title}"`}
                      >
                        Read Essay
                        <svg
                          className="h-4 w-4 transition-transform group-hover/link:translate-x-1"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M17 8l4 4m0 0l-4 4m4-4H3"
                          />
                        </svg>
                      </Link>
                    </div>
                  </article>
                </li>
              )
            })}
          </ul>
          {pagination && pagination.totalPages > 1 && (
            <div className="glass-panel-enhanced animate-diagonal-open mt-8 rounded-xl p-4">
              <Pagination currentPage={pagination.currentPage} totalPages={pagination.totalPages} />
            </div>
          )}
        </div>
      </div>
    </>
  )
}
