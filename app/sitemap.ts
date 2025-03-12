import { MetadataRoute } from 'next'
import { allEssays } from 'contentlayer/generated'
import siteMetadata from '@/data/siteMetadata'
import { leetcodeSolutions } from '@/data/projectsData'

export const dynamic = 'force-static'

export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = siteMetadata.siteUrl

  const blogRoutes = allEssays
    .filter((post) => !post.draft)
    .map((post) => ({
      url: `${siteUrl}${post.path}`,
      lastModified: post.lastmod || post.date,
    }))

  const routes = [
    '',
    'essays',
    'projects',
    'tags',
    'about',
    'bookmarks',
    'static/resume/prakash_s_resume.pdf',
    'leetcode-solutions',
    ...leetcodeSolutions.map((solution) => solution.href),
  ].map((route) => ({
    url: `${siteUrl}${route}`,
    lastModified: new Date().toISOString().split('T')[0],
  }))

  return [...routes, ...blogRoutes]
}
