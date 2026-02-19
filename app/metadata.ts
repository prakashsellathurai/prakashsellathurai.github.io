import { Metadata } from 'next'
import siteMetadata from '@/data/siteMetadata'

export const metadata: Metadata = {
  title: `${siteMetadata.title} - Home`,
  description: siteMetadata.description,
  keywords: siteMetadata.keywords,
}
