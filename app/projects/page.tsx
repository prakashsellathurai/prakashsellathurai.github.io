import { projectsData as fallbackProjectsData, Project } from '@/data/projectsData'
import { genPageMetadata } from 'app/seo'
import { Thing, WithContext } from 'schema-dts'
import ProjectsClient from '@/components/ProjectsClient'

export const metadata = genPageMetadata({ title: 'Projects' })

import { getProjects } from '@/lib/data'

export default async function Projects() {
  const projectsData = await getProjects(true)
  const structuredData: WithContext<Thing>[] = projectsData.map((project) => ({
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: project.title,
    description: project.description,
    url: project.href,
    image: project.imgSrc,
    offers: {
      '@type': 'Offer',
      price: 0,
      priceCurrency: 'USD',
    },
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: 5,
      ratingCount: Math.max(project.stars || 0, 1),
    },
  }))

  // Calculate total stats
  const totalStars = projectsData.reduce((sum, project) => sum + (project.stars || 0), 0)
  const totalProjects = projectsData.length

  return (
    <>
      <div className="divide-y divide-black/10 dark:divide-white/10">
        {/* Enhanced Header */}
        <div className="space-y-4 pb-8 pt-6 md:space-y-6">
          <h1 className="bg-gradient-to-r from-black via-primary-600 to-secondary-600 bg-clip-text text-4xl font-extrabold leading-tight tracking-tight text-transparent dark:from-white dark:via-primary-400 dark:to-secondary-400 sm:text-5xl md:text-6xl md:leading-tight">
            Projects Portfolio
          </h1>

          {/* Stats Row */}
          <div className="flex flex-wrap gap-6 text-sm md:text-base">
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/30">
                <svg
                  className="h-5 w-5 text-primary-600 dark:text-primary-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M2 6a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 100 4v2a2 2 0 01-2 2H4a2 2 0 01-2-2v-2a2 2 0 100-4V6z" />
                </svg>
              </div>
              <div>
                <div className="font-bold text-black dark:text-white">{totalProjects}</div>
                <div className="text-xs text-black dark:text-white">Projects</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-yellow-100 dark:bg-yellow-900/30">
                <svg
                  className="h-5 w-5 text-yellow-600 dark:text-yellow-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </div>
              <div>
                <div className="font-bold text-black dark:text-white">{totalStars}</div>
                <div className="text-xs text-black dark:text-white">Total Stars</div>
              </div>
            </div>
          </div>

          <p className="text-base leading-7 text-black dark:text-white md:text-lg">
            Explore my open-source projects and contributions, dynamically fetched from{' '}
            <a
              href="https://github.com/prakashsellathurai"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-primary-500 transition-colors hover:text-primary-600 hover:underline dark:hover:text-primary-400"
            >
              GitHub
            </a>
            . Each project showcases different technologies, frameworks, and problem-solving
            approaches.
          </p>
        </div>

        {/* Projects with Filters */}
        <div className="pt-8">
          <div className="glass-panel-enhanced rounded-3xl p-8 md:p-10">
            <ProjectsClient projects={projectsData} />
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
