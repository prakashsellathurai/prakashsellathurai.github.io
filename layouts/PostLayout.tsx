import { ReactNode } from 'react'
import { CoreContent } from 'pliny/utils/contentlayer'
import type { Essay, Authors } from 'contentlayer/generated'
import Comments from '@/components/Comments'
import Link from '@/components/Link'
import PageTitle from '@/components/PageTitle'
import SectionContainer from '@/components/SectionContainer'
import Image from '@/components/Image'
import Tag from '@/components/Tag'
import siteMetadata from '@/data/siteMetadata'
import ScrollTopAndComment from '@/components/ScrollTopAndComment'

const editUrl = (path) => `${siteMetadata.siteRepo}/blob/main/data/${path}`
const discussUrl = (path) =>
  `https://mobile.twitter.com/search?q=${encodeURIComponent(`${siteMetadata.siteUrl}/${path}`)}`

const postDateTemplate: Intl.DateTimeFormatOptions = {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
}

interface LayoutProps {
  content: CoreContent<Essay>
  authorDetails: CoreContent<Authors>[]
  next?: { path: string; title: string }
  prev?: { path: string; title: string }
  children: ReactNode
}

export default function PostLayout({ content, authorDetails, next, prev, children }: LayoutProps) {
  const { filePath, path, slug, date, title, tags } = content
  const basePath = path.split('/')[0]

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-8 lg:flex-row">
        {/* Main Article Content */}
        <div className="w-full lg:w-3/4">
          <div className="card-simple">
            <header className="mb-8 border-b border-gray-200 pb-8 dark:border-gray-700">
              <div className="mb-2 text-center text-sm text-gray-500 dark:text-gray-400">
                <time dateTime={date}>
                  {new Date(date).toLocaleDateString(siteMetadata.locale, postDateTemplate)}
                </time>
              </div>
              <h1 className="text-center text-3xl font-extrabold leading-9 tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl sm:leading-10 md:text-5xl md:leading-14">
                {title}
              </h1>
            </header>

            <div className="prose max-w-none dark:prose-invert">{children}</div>

            <div className="mt-8 border-t border-gray-200 pt-8 dark:border-gray-700">
              <div className="flex flex-wrap gap-2 text-sm">
                <span className="font-bold text-gray-700 dark:text-gray-300">Tags:</span>
                {tags?.map((tag) => (
                  <Tag key={tag} text={tag} />
                ))}
              </div>

              <div className="mt-8 flex justify-between">
                {prev && prev.path && (
                  <div className="text-left">
                    <div className="text-xs text-gray-500">Previous Essay</div>
                    <div className="text-primary-500 hover:text-primary-600">
                      <Link href={`/${prev.path}`}>{prev.title}</Link>
                    </div>
                  </div>
                )}
                {next && next.path && (
                  <div className="text-right">
                    <div className="text-xs text-gray-500">Next Essay</div>
                    <div className="text-primary-500 hover:text-primary-600">
                      <Link href={`/${next.path}`}>{next.title}</Link>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar (Author Info) */}
        <div className="w-full space-y-6 lg:w-1/4">
          <div className="card-simple">
            <div className="mb-4 border-b border-gray-200 pb-2 dark:border-gray-700">
              <h3 className="text-sm font-bold text-gray-700 dark:text-gray-200">About Author</h3>
            </div>
            <div className="flex flex-col items-center">
              {authorDetails.map((author) => (
                <div key={author.name} className="contents">
                  {author.avatar && (
                    <Image
                      src={author.avatar}
                      width={80}
                      height={80}
                      alt="avatar"
                      className="mb-4 h-20 w-20 rounded-full"
                    />
                  )}
                  <h4 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                    {author.name}
                  </h4>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {author.occupation}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="card-simple">
            <div className="mb-4 border-b border-gray-200 pb-2 dark:border-gray-700">
              <h3 className="text-sm font-bold text-gray-700 dark:text-gray-200">Navigation</h3>
            </div>
            <Link href="/essays" className="block text-primary-500 hover:underline">
              &larr; Back to Essays
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
