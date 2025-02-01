import React from 'react'
import Card from './Card'
import Image from './Image'
import Link from './Link'
import { sampleProjects } from '@/data/projectsData'

const SampleProjects: React.FC = () => {
  return (
    <>
      <h2 className="mb-6 mt-12 text-3xl font-bold">Projects</h2>

      <div className="container mb-6 ">
        <div className="grid grid-cols-1 gap-8">
          {sampleProjects.map((d) => (
            <div
              key={d.title}
              className={`${
                d.imgSrc && 'h-full'
              }  size-full overflow-hidden rounded-bl-3xl border-b-2 border-l-2 border-gray-200 border-opacity-60 dark:border-gray-700`}
            >
              {d.imgSrc &&
                (d.href ? (
                  <Link href={d.href} aria-label={`Link to ${d.title}`}>
                    <Image
                      alt={d.title}
                      src={d.imgSrc}
                      className="object-cover object-center md:h-36 lg:h-48"
                      width={544}
                      height={306}
                    />
                  </Link>
                ) : (
                  <Image
                    alt={d.title}
                    src={d.imgSrc}
                    className="object-cover object-center md:h-36 lg:h-48"
                    width={544}
                    height={306}
                  />
                ))}
              <div className="p-6">
                <h2 className="mb-3 text-2xl font-bold leading-8 tracking-tight">
                  {d.href ? (
                    <Link href={d.href} aria-label={`Link to ${d.title}`}>
                      {d.title}
                    </Link>
                  ) : (
                    d.title
                  )}
                </h2>
                <p className="prose mb-3 max-w-none text-gray-500 dark:text-gray-400">
                  {d.description}
                </p>
                {d.href && (
                  <Link
                    href={d.href}
                    className="text-base font-medium leading-6 text-primary-500 hover:text-primary-600 dark:hover:text-primary-400"
                    aria-label={`Link to ${d.title}`}
                  >
                    Learn more &rarr;
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-center py-3 text-sm text-gray-800 before:me-6 before:flex-1 before:border-t before:border-gray-200 after:ms-6 after:flex-1 after:border-t after:border-gray-200 dark:text-white dark:before:border-neutral-600 dark:after:border-neutral-600">
        {' '}
        <a href="./projects">Read More</a>
      </div>
    </>
  )
}

export default SampleProjects
