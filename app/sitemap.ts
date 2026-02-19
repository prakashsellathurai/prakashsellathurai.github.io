import { MetadataRoute } from 'next'
import { allEssays } from 'contentlayer/generated'
import siteMetadata from '@/data/siteMetadata'
import { leetcodeSolutions, projectsData } from '@/data/projectsData'

export const dynamic = 'force-static'

export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = siteMetadata.siteUrl.endsWith('/')
    ? siteMetadata.siteUrl.slice(0, -1)
    : siteMetadata.siteUrl

  const blogRoutes = allEssays
    .filter((post) => !post.draft)
    .map((post) => ({
      url: `${siteUrl}/${post.path}`,
      lastModified: post.lastmod || post.date,
      changeFrequency: 'monthly' as const,
      priority: 0.7,
    }))

  const projectRoutes = projectsData
    .filter(
      (project) =>
        project.website && project.website.startsWith('http') && project.website.startsWith(siteUrl)
    )
    .map((project) => ({
      url: project.website as string,
      lastModified: new Date().toISOString().split('T')[0],
      changeFrequency: 'monthly' as const,
      priority: 0.6,
    }))

  const routes = [
    { path: '', priority: 1.0, changeFrequency: 'daily' as const },
    { path: 'about', priority: 0.9, changeFrequency: 'monthly' as const },
    { path: 'essays', priority: 0.8, changeFrequency: 'weekly' as const },
    { path: 'projects', priority: 0.8, changeFrequency: 'weekly' as const },
    { path: 'tags', priority: 0.5, changeFrequency: 'weekly' as const },
    { path: 'bookmarks', priority: 0.5, changeFrequency: 'weekly' as const },
    { path: 'leetcode-solutions', priority: 0.6, changeFrequency: 'weekly' as const },
    {
      path: 'static/resume/prakash_s_resume.pdf',
      priority: 0.7,
      changeFrequency: 'monthly' as const,
    },
  ].map((route) => ({
    url: `${siteUrl}/${route.path}`,
    lastModified: new Date().toISOString().split('T')[0],
    changeFrequency: route.changeFrequency,
    priority: route.priority,
  }))

  const leetcodeRoutes = leetcodeSolutions.map((solution) => ({
    url: `${siteUrl}/${solution.href}`,
    lastModified: new Date().toISOString().split('T')[0],
    changeFrequency: 'monthly' as const,
    priority: 0.5,
  }))

  return [...routes, ...blogRoutes, ...projectRoutes, ...leetcodeRoutes]
}
