import { Authors, allAuthors } from 'contentlayer/generated'
import { MDXLayoutRenderer } from 'pliny/mdx-components'
import AuthorLayout from '@/layouts/AuthorLayout'
import { coreContent } from 'pliny/utils/contentlayer'
import { genPageMetadata } from 'app/seo'

import { Metadata } from 'next'
export const metadata: Metadata = genPageMetadata({ title: 'About', canonical: '/about' })

export default function Page() {
  const author = allAuthors.find((p) => p.slug === 'default') as Authors
  const mainContent = coreContent(author)

  return (
    <div className="glass-panel-enhanced my-8 rounded-3xl p-8 md:p-10">
      {/* Enhanced Header */}
      <div className="mb-8 space-y-2 border-b border-black/10 pb-8 pt-6 dark:border-white/10 md:space-y-5">
        <h1 className="bg-gradient-to-r from-black via-primary-600 to-secondary-600 bg-clip-text text-3xl font-extrabold leading-9 tracking-tight text-transparent dark:from-white dark:via-primary-400 dark:to-secondary-400 sm:text-4xl sm:leading-10 md:text-6xl md:leading-14">
          About Me
        </h1>
      </div>
      <AuthorLayout content={mainContent}>
        <MDXLayoutRenderer code={author.body.code} />
      </AuthorLayout>
    </div>
  )
}
