'use client'

import { usePathname } from 'next/navigation'
import { slug } from 'github-slugger'
import { formatDate } from 'pliny/utils/formatDate'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Essay } from 'contentlayer/generated'
import Link from '@/components/Link'
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
  const basePath = pathname.replace(/^\//, '').replace(/\/page\/\d+$/, '')
  const prevPage = currentPage - 1 > 0
  const nextPage = currentPage + 1 <= totalPages

  return (
    <div className="space-y-2 pb-8 pt-6 md:space-y-5">
      <nav className="flex justify-between">
        {!prevPage && (
          <button className="cursor-auto disabled:opacity-50" disabled={!prevPage}>
            &larr; Previous
          </button>
        )}
        {prevPage && (
          <Link
            href={currentPage - 1 === 1 ? `/${basePath}/` : `/${basePath}/page/${currentPage - 1}`}
            rel="prev"
            className="text-primary-500 hover:underline"
          >
            &larr; Previous
          </Link>
        )}
        <span>
          {currentPage} of {totalPages}
        </span>
        {!nextPage && (
          <button className="cursor-auto disabled:opacity-50" disabled={!nextPage}>
            Next &rarr;
          </button>
        )}
        {nextPage && (
          <Link
            href={`/${basePath}/page/${currentPage + 1}`}
            rel="next"
            className="text-primary-500 hover:underline"
          >
            Next &rarr;
          </Link>
        )}
      </nav>
    </div>
  )
}

export default function ListLayoutWithTags({
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
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-8 lg:flex-row">
        {/* Main Content */}
        <div className="w-full lg:w-3/4">
          <div className="card-simple">
            <div className="mb-4 border-b border-gray-200 pb-2 dark:border-gray-700">
              <h1 className="text-2xl font-bold text-primary-500">{title}</h1>
            </div>

            <div className="space-y-4">
              {displayPosts.map((post) => {
                const { path, date, title, summary, tags } = post
                return (
                  <div
                    key={path}
                    className="flex flex-col gap-1 border-b border-gray-100 pb-4 last:border-0 dark:border-gray-800"
                  >
                    <div className="flex items-baseline justify-between">
                      <h2 className="text-2xl font-bold text-primary-600 hover:text-primary-800 dark:text-primary-400">
                        <Link href={`/${path}`}>{title}</Link>
                      </h2>
                      <time className="shrink-0 text-base text-gray-500" dateTime={date}>
                        {formatDate(date, siteMetadata.locale)}
                      </time>
                    </div>
                    <p className="text-gray-700 dark:text-gray-300">{summary}</p>
                    <div className="flex gap-2">
                      {tags?.map((tag) => (
                        <span key={tag} className="text-sm text-secondary-500">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
            {pagination && pagination.totalPages > 1 && (
              <Pagination currentPage={pagination.currentPage} totalPages={pagination.totalPages} />
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-full space-y-6 lg:w-1/4">
          <div className="card-simple">
            <div className="mb-4 border-b border-gray-200 pb-2 dark:border-gray-700">
              <h3 className="text-sm font-bold text-gray-700 dark:text-gray-200">Filter by Tag</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                href={`/essays`}
                className={`text-xs ${pathname === '/essays' ? 'font-bold text-primary-600' : 'text-primary-500 hover:underline'}`}
              >
                All Essays ({posts.length})
              </Link>
              {sortedTags.map((t) => {
                const isSelected = decodeURI(pathname.split('/tags/')[1]) === slug(t)
                return (
                  <Link
                    key={t}
                    href={`/tags/${slug(t)}`}
                    className={`text-xs ${isSelected ? 'font-bold text-primary-600' : 'text-primary-500 hover:underline'}`}
                  >
                    {t} ({tagCounts[t]})
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
