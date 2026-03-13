import { Metadata } from 'next'
import siteMetadata from '@/data/siteMetadata'

interface PageSEOProps {
  title: string
  description?: string
  image?: string
  keywords?: string[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any
}

export function genPageMetadata({
  title,
  description,
  image,
  keywords,
  canonical,
  ...rest
}: PageSEOProps & { canonical?: string }): Metadata {
  return {
    title,
    description: description || siteMetadata.description,
    keywords: keywords || siteMetadata.keywords,
    openGraph: {
      title: `${title} | ${siteMetadata.title}`,
      description: description || siteMetadata.description,
      url: canonical ? `${siteMetadata.siteUrl}${canonical}` : './',
      siteName: siteMetadata.title,
      images: image ? [image] : [siteMetadata.socialBanner],
      locale: 'en_US',
      type: 'website',
    },
    alternates: canonical
      ? {
          canonical: `${siteMetadata.siteUrl}${canonical}`,
        }
      : undefined,
    twitter: {
      title: `${title} | ${siteMetadata.title}`,
      card: 'summary_large_image',
      images: image ? [image] : [siteMetadata.socialBanner],
      creator: '@prakashsellathurai',
    },
    ...rest,
  }
}
