'use client'

import { useState, useMemo } from 'react'
import Card from '@/components/Card'
import { Project } from '@/data/projectsData'

interface ProjectsClientProps {
  projects: Project[]
}

export default function ProjectsClient({ projects }: ProjectsClientProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'stars' | 'updated' | 'name'>('stars')

  // Extract unique languages from projects
  const languages = useMemo(() => {
    const langs = new Set<string>()
    projects.forEach((project) => {
      if (project.language) langs.add(project.language)
    })
    return ['all', ...Array.from(langs).sort()]
  }, [projects])

  // Filter and sort projects
  const filteredProjects = useMemo(() => {
    const filtered = projects.filter((project) => {
      const matchesSearch =
        searchTerm === '' ||
        project.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        project.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        project.tags?.some((tag) => tag.toLowerCase().includes(searchTerm.toLowerCase()))

      const matchesLanguage = selectedLanguage === 'all' || project.language === selectedLanguage

      return matchesSearch && matchesLanguage
    })

    // Sort projects
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'stars':
          return (b.stars || 0) - (a.stars || 0)
        case 'updated':
          if (!a.updatedAt || !b.updatedAt) return 0
          return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
        case 'name':
          return a.title.localeCompare(b.title)
        default:
          return 0
      }
    })

    return filtered
  }, [projects, searchTerm, selectedLanguage, sortBy])

  return (
    <>
      {/* Filters Section */}
      <div className="mb-8 space-y-4 rounded-2xl border border-gray-200/60 bg-white/60 p-6 backdrop-blur-md dark:border-gray-700/60 dark:bg-gray-800/40">
        {/* Search Bar */}
        <div className="relative">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
            <svg
              className="h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search projects by name, description, or tags..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl border border-gray-300 bg-white py-3 pl-12 pr-4 text-gray-900 placeholder-gray-500 transition-all duration-300 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 dark:border-gray-600 dark:bg-gray-700/50 dark:text-gray-100 dark:placeholder-gray-400 dark:focus:border-primary-400"
          />
        </div>

        {/* Filters Row */}
        <div className="flex flex-wrap items-center gap-4">
          {/* Language Filter */}
          <div className="flex items-center gap-2">
            <label
              htmlFor="language-filter"
              className="text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Language:
            </label>
            <select
              id="language-filter"
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-all duration-300 hover:border-primary-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
            >
              {languages.map((lang) => (
                <option key={lang} value={lang}>
                  {lang === 'all' ? 'All Languages' : lang}
                </option>
              ))}
            </select>
          </div>

          {/* Sort Filter */}
          <div className="flex items-center gap-2">
            <label
              htmlFor="sort-filter"
              className="text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Sort by:
            </label>
            <select
              id="sort-filter"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'stars' | 'updated' | 'name')}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-all duration-300 hover:border-primary-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
            >
              <option value="stars">Most Stars</option>
              <option value="updated">Recently Updated</option>
              <option value="name">Name (A-Z)</option>
            </select>
          </div>

          {/* Results Count */}
          <div className="ml-auto text-sm text-gray-600 dark:text-gray-400">
            Showing{' '}
            <span className="font-semibold text-primary-600 dark:text-primary-400">
              {filteredProjects.length}
            </span>{' '}
            of {projects.length} projects
          </div>
        </div>

        {/* Active Filters - Clear All */}
        {(searchTerm || selectedLanguage !== 'all') && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Active filters:</span>
            {searchTerm && (
              <span className="inline-flex items-center gap-1 rounded-full bg-primary-100 px-3 py-1 text-xs font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
                Search: "{searchTerm}"
                <button
                  onClick={() => setSearchTerm('')}
                  className="ml-1 hover:text-primary-900 dark:hover:text-primary-100"
                  aria-label="Clear search"
                >
                  ×
                </button>
              </span>
            )}
            {selectedLanguage !== 'all' && (
              <span className="inline-flex items-center gap-1 rounded-full bg-primary-100 px-3 py-1 text-xs font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
                {selectedLanguage}
                <button
                  onClick={() => setSelectedLanguage('all')}
                  className="ml-1 hover:text-primary-900 dark:hover:text-primary-100"
                  aria-label="Clear language filter"
                >
                  ×
                </button>
              </span>
            )}
            <button
              onClick={() => {
                setSearchTerm('')
                setSelectedLanguage('all')
              }}
              className="text-xs text-primary-600 hover:underline dark:text-primary-400"
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Projects Grid */}
      {filteredProjects.length > 0 ? (
        <div className="container py-8">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredProjects.map((project) => (
              <Card
                key={project.title}
                title={project.title}
                description={project.description}
                imgSrc={project.imgSrc}
                href={project.href}
                stars={project.stars}
                language={project.language}
                forks={project.forks}
                tags={project.tags}
                updatedAt={project.updatedAt}
              />
            ))}
          </div>
        </div>
      ) : (
        // Empty State
        <div className="flex min-h-[400px] flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-300 bg-gray-50/50 p-12 text-center dark:border-gray-700 dark:bg-gray-800/20">
          <svg
            className="mb-4 h-16 w-16 text-gray-400 dark:text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="mb-2 text-xl font-semibold text-gray-700 dark:text-gray-300">
            No projects found
          </h3>
          <p className="mb-4 text-gray-500 dark:text-gray-400">
            Try adjusting your filters or search term
          </p>
          <button
            onClick={() => {
              setSearchTerm('')
              setSelectedLanguage('all')
            }}
            className="rounded-lg bg-primary-500 px-6 py-2 text-white transition-colors duration-300 hover:bg-primary-600 dark:bg-primary-600 dark:hover:bg-primary-500"
          >
            Clear all filters
          </button>
        </div>
      )}
    </>
  )
}
