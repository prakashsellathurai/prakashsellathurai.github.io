import Link from '@/components/Link'
import Tag from '@/components/Tag'
import siteMetadata from '@/data/siteMetadata'
import { formatDate } from 'pliny/utils/formatDate'
import NewsletterForm from 'pliny/ui/NewsletterForm'
import { allAuthors, Authors } from 'contentlayer/generated'
import { coreContent } from 'pliny/utils/contentlayer'
import AuthorLayout from '@/layouts/AuthorLayout'
import { MDXLayoutRenderer } from 'pliny/mdx-components'
import Bookshelf from '@/components/books'
import SampleProjects from '@/components/SampleProjects'
import { BlogPosting, WithContext } from 'schema-dts'

const MAX_DISPLAY = 5

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
      {/* Enhanced Hero Section with Author Info */}
      <div className="hero-section relative mb-16 overflow-hidden rounded-3xl">
        {/* Animated gradient background - Neutral Primary */}
        <div className="animate-gradient-shift absolute inset-0 bg-gradient-to-br from-primary-500/10 via-primary-400/5 to-primary-500/10" />

        {/* Glass panel overlay - Lower opacity for B&W Blueprint */}
        <div className="animate-diagonal-open relative rounded-3xl border border-black/10 bg-white/20 p-8 shadow-xl backdrop-blur-xl dark:border-white/10 dark:bg-black/20 md:p-12">
          {/* Floating corner accents - Secondary */}
          <div className="absolute left-4 top-4 h-16 w-16 rounded-tl-2xl border-l-2 border-t-2 border-primary-400/30" />
          <div className="absolute bottom-4 right-4 h-16 w-16 rounded-br-2xl border-b-2 border-r-2 border-primary-400/30" />

          <AuthorLayout content={mainContent}>
            <MDXLayoutRenderer code={author.body.code} />
          </AuthorLayout>
        </div>
      </div>

      {/* Latest Essays Section */}
      <section className="section-fade-in relative mb-16 overflow-hidden rounded-3xl">
        {/* Animated gradient background - Consistency with Hero */}
        <div className="animate-gradient-shift absolute inset-0 bg-gradient-to-br from-primary-500/10 via-primary-400/5 to-primary-500/10" />

        <div className="glass-panel-enhanced animate-diagonal-open relative rounded-3xl p-8 md:p-10">
          {/* Section header with decorative line */}
          <div className="relative mb-12">
            <div className="flex items-center gap-4">
              <div className="h-1 w-12 rounded-full bg-primary-500/40" />
              <h2 className="text-4xl font-extrabold tracking-tight text-black dark:text-white md:text-5xl">
                Latest Essays
              </h2>
            </div>
            <div className="mt-3 h-px bg-primary-500/20" />
          </div>

          {/* Essays grid */}
          <ul className="space-y-8">
            {!posts.length && (
              <p className="py-12 text-center text-black/50 dark:text-white/50">No posts found.</p>
            )}
            {posts.slice(0, MAX_DISPLAY).map((post, index) => {
              const { slug, date, title, summary, tags } = post
              return (
                <li
                  key={slug}
                  className="essay-card animate-diagonal-open group relative overflow-hidden rounded-2xl border border-black/5 bg-white/20 backdrop-blur-xl transition-all duration-500 hover:scale-[1.01] hover:border-black/20 hover:shadow-xl dark:border-white/5 dark:bg-black/20"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  {/* Hover effect */}
                  <div className="absolute inset-0 rounded-2xl bg-secondary-500/0 transition-all duration-500 group-hover:bg-secondary-500/5" />

                  <article className="relative p-6 md:p-8">
                    <div className="space-y-4 xl:grid xl:grid-cols-4 xl:items-start xl:gap-8 xl:space-y-0">
                      {/* Date badge */}
                      <div className="flex items-start">
                        <time
                          dateTime={date}
                          className="inline-flex items-center gap-2 rounded-xl bg-primary-100/80 px-4 py-2 text-sm font-semibold text-primary-700 backdrop-blur-sm dark:bg-primary-900/30 dark:text-primary-300"
                        >
                          <svg
                            className="h-4 w-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                            />
                          </svg>
                          {formatDate(date, siteMetadata.locale)}
                        </time>
                      </div>

                      {/* Content */}
                      <div className="space-y-4 xl:col-span-3">
                        <div className="space-y-3">
                          <h3 className="text-2xl font-bold leading-tight tracking-tight md:text-3xl">
                            <Link
                              href={`/essays/${slug}`}
                              className="text-black transition-colors duration-300 group-hover:text-primary-600 dark:text-white dark:group-hover:text-primary-400"
                            >
                              {title}
                            </Link>
                          </h3>

                          {/* Tags */}
                          {tags && tags.length > 0 && (
                            <div className="flex flex-wrap gap-2">
                              {tags.map((tag) => (
                                <span
                                  key={tag}
                                  className="inline-flex cursor-pointer items-center rounded-full border border-black/10 bg-black/5 px-3 py-1 text-xs font-medium text-black/70 backdrop-blur-sm transition-colors duration-300 hover:bg-primary-100 hover:text-primary-700 dark:border-white/10 dark:bg-white/5 dark:text-white/70 dark:hover:bg-primary-900/30 dark:hover:text-primary-300"
                                >
                                  <span className="mr-1">#</span>
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Summary */}
                        <p className="prose line-clamp-2 max-w-none leading-relaxed text-black/70 dark:prose-invert dark:text-white/70">
                          {summary}
                        </p>

                        {/* Read more link */}
                        <Link
                          href={`/essays/${slug}`}
                          className="group/link inline-flex items-center gap-2 text-base font-semibold text-black transition-all duration-300 hover:gap-3 hover:text-primary-600 dark:text-white dark:hover:text-primary-400"
                          aria-label={`Read more: "${title}"`}
                        >
                          <span>Read more</span>
                          <svg
                            className="h-5 w-5 transition-transform duration-300 group-hover/link:translate-x-1"
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
                      </div>
                    </div>
                  </article>

                  {/* Corner decorations */}
                  <div className="absolute right-2 top-2 h-8 w-8 rounded-tr-lg border-r border-t border-primary-400/0 transition-all duration-500 group-hover:border-primary-400/30" />
                  <div className="absolute bottom-2 left-2 h-8 w-8 rounded-bl-lg border-b border-l border-primary-400/0 transition-all duration-500 group-hover:border-primary-400/30" />
                </li>
              )
            })}
          </ul>

          {/* View all essays link */}
          {posts.length > MAX_DISPLAY && (
            <div className="mt-10 flex justify-center">
              <Link
                href="/essays"
                className="group inline-flex items-center gap-3 rounded-full bg-black px-8 py-4 text-base font-bold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:bg-black/80 dark:bg-white dark:text-black dark:hover:bg-white/80"
                aria-label="All posts"
              >
                <span>View All Essays</span>
                <svg
                  className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1"
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
            </div>
          )}
        </div>
      </section>

      {/* Bookshelf Section */}
      <section
        className="section-fade-in relative mb-16 overflow-hidden rounded-3xl"
        style={{ animationDelay: '0.2s' }}
      >
        {/* Animated gradient background - Consistency with Hero */}
        <div className="animate-gradient-shift absolute inset-0 bg-gradient-to-br from-secondary-500/10 via-secondary-400/5 to-secondary-500/10" />

        <div className="glass-panel-enhanced animate-diagonal-open relative rounded-3xl p-8 md:p-10">
          <div className="relative mb-8">
            <div className="flex items-center gap-4">
              <div className="h-1 w-12 rounded-full bg-secondary-500/40" />
              <h2 className="text-3xl font-extrabold tracking-tight text-black dark:text-white md:text-4xl">
                Reading List
              </h2>
            </div>
          </div>
          <Bookshelf books={books.slice(0, 6)} />
        </div>
      </section>

      {/* Projects Section */}
      <section
        className="section-fade-in relative mb-16 overflow-hidden rounded-3xl"
        style={{ animationDelay: '0.3s' }}
      >
        {/* Animated gradient background - Consistency with Hero */}
        <div className="animate-gradient-shift absolute inset-0 bg-gradient-to-br from-primary-500/10 via-primary-400/5 to-primary-500/10" />

        <div className="glass-panel-enhanced animate-diagonal-open relative rounded-3xl p-8 md:p-10">
          <div className="relative mb-8">
            <div className="flex items-center gap-4">
              <div className="h-1 w-12 rounded-full bg-primary-500/40" />
              <h2 className="text-3xl font-extrabold tracking-tight text-black dark:text-white md:text-4xl">
                Featured Projects
              </h2>
            </div>
          </div>
          <SampleProjects projects={projects.slice(0, 6)} />
        </div>
      </section>

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
    </>
  )
}
