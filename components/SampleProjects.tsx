import React from 'react'
import Image from './Image'
import Link from './Link'
import { Project } from '@/data/projectsData'

const SampleProjects: React.FC<{ projects: Project[] }> = ({ projects }) => {
  return (
    <div className="grid grid-cols-1 gap-8">
      {projects.map((d) => (
        <div
          key={d.title}
          className={`${
            d.imgSrc && 'h-full'
          } card-project group relative flex size-full flex-col overflow-hidden rounded-3xl border border-black/10 bg-white/20 backdrop-blur-xl transition-all duration-500 hover:scale-[1.02] hover:border-black/20 hover:shadow-xl dark:border-white/10 dark:bg-black/20`}
        >
          {/* Hover glow effect - Neutral Primary */}
          <div className="pointer-events-none absolute inset-0 rounded-3xl opacity-0 transition-opacity duration-500 group-hover:opacity-100">
            <div className="absolute inset-0 rounded-3xl bg-primary-500/5" />
          </div>

          {d.imgSrc &&
            (d.href ? (
              <Link
                href={d.href}
                aria-label={`Link to ${d.title}`}
                className="relative block overflow-hidden"
              >
                <Image
                  alt={d.title}
                  src={d.imgSrc}
                  className="w-full object-cover object-center transition-transform duration-700 group-hover:scale-110 md:h-48 lg:h-64"
                  width={544}
                  height={306}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
              </Link>
            ) : (
              <div className="relative overflow-hidden">
                <Image
                  alt={d.title}
                  src={d.imgSrc}
                  className="w-full object-cover object-center transition-transform duration-700 group-hover:scale-110 md:h-48 lg:h-64"
                  width={544}
                  height={306}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
              </div>
            ))}

          <div className="relative flex flex-1 flex-col p-6">
            <h2 className="mb-3 text-2xl font-bold leading-8 tracking-tight transition-colors duration-300 group-hover:text-primary-600 dark:group-hover:text-primary-400">
              {d.href ? (
                <Link href={d.href} aria-label={`Link to ${d.title}`}>
                  {d.title}
                </Link>
              ) : (
                d.title
              )}
            </h2>
            <p className="prose mb-4 line-clamp-3 flex-1 text-black/50 dark:text-white/40">
              {d.description}
            </p>
            {d.href && (
              <div className="mt-auto pt-4">
                <Link
                  href={d.href}
                  className="group/link inline-flex items-center gap-1 text-base font-medium leading-6 text-black transition-all duration-300 hover:gap-2 hover:text-primary-600 dark:text-white dark:hover:text-primary-400"
                  aria-label={`Link to ${d.title}`}
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
              </div>
            )}
          </div>

          {/* Blueprint-style corner brackets - Neutral Secondary */}
          <div className="pointer-events-none absolute left-2 top-2 h-4 w-4 border-l border-t border-primary-400/20 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
          <div className="pointer-events-none absolute bottom-2 right-2 h-4 w-4 border-b border-r border-primary-400/20 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
        </div>
      ))}
    </div>
  )
}

export default SampleProjects
