import Link from '@/components/Link'
import Tag from '@/components/Tag'
import { slug } from 'github-slugger'
import tagData from 'app/tag-data.json'
import { genPageMetadata } from 'app/seo'

export const metadata = genPageMetadata({ title: 'Tags', description: 'Things I blog about' })

export default async function Page() {
  const tagCounts = tagData as Record<string, number>
  const tagKeys = Object.keys(tagCounts)
  const sortedTags = tagKeys.sort((a, b) => tagCounts[b] - tagCounts[a])
  return (
    <>
      <div className="glass-panel-enhanced my-8 rounded-3xl p-8 md:p-10">
        {/* Enhanced Header */}
        <div className="mb-8 space-y-2 border-b border-gray-200/60 pb-8 pt-6 dark:border-gray-700/60 md:space-y-5">
          <h1 className="bg-gradient-to-r from-gray-900 via-primary-600 to-secondary-600 bg-clip-text text-3xl font-extrabold leading-9 tracking-tight text-transparent dark:from-gray-100 dark:via-primary-400 dark:to-secondary-400 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14">
            Tags
          </h1>
        </div>

        <div className="flex flex-wrap gap-4">
          {tagKeys.length === 0 && 'No tags found.'}
          {sortedTags.map((t) => {
            return (
              <div key={t} className="mb-2 mr-5 mt-2">
                <Tag text={t} />
                <Link
                  href={`/tags/${slug(t)}`}
                  className="-ml-2 text-sm font-semibold uppercase text-gray-600 transition-colors hover:text-primary-500 dark:text-gray-300 dark:hover:text-primary-400"
                  aria-label={`View posts tagged ${t}`}
                >
                  {` (${tagCounts[t]})`}
                </Link>
              </div>
            )
          })}
        </div>
      </div>
    </>
  )
}
