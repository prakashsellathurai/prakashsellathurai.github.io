import { ReactNode } from 'react'
import type { Authors } from 'contentlayer/generated'
import SocialIcon from '@/components/social-icons'
import Image from '@/components/Image'
import { Person, WithContext, ProfilePage } from 'schema-dts'
import { siteUrl } from '@/data/siteMetadata'

interface Props {
  children: ReactNode
  content: Omit<Authors, '_id' | '_raw' | 'body'>
}

export default function AuthorLayout({ children, content }: Props) {
  const { name, avatar, occupation, company, email, twitter, bluesky, linkedin, github } = content

  const structuredData: WithContext<ProfilePage> = {
    '@context': 'https://schema.org',
    '@type': 'ProfilePage',
    dateCreated: '2024-12-23T12:34:00-05:00',
    dateModified: '2024-12-26T14:53:00-05:00',
    mainEntity: {
      '@type': 'Person',
      name: name,
      alternateName: 'Prakash S', // Replace with actual alternate name if available
      identifier: '123475623', // Replace with actual identifier if available
      description:
        'Prakash is a Software Engineer with a multidisciplinary background in Mechatronics, specializing in Computer Vision and Python. He has worked at Amazon and Bigthinx, and co-founded ClothX. His interests include software engineering, information theory, and automation projects.',
      image: avatar,
      url: siteUrl,
      sameAs: [github, linkedin, twitter, bluesky].filter((url): url is string => !!url), // Filter out any undefined or empty values
    },
  }

  return (
    <>
      <div className="divide-y divide-gray-200 dark:divide-gray-700 ">
        <div className="items-start space-y-2 rounded-2xl bg-gray-50 p-8 xl:grid xl:grid-cols-3 xl:gap-x-8 xl:space-y-0">
          <div className="flex flex-col items-center space-x-2 pt-8">
            {avatar && (
              <Image
                src={avatar}
                alt="avatar"
                width={192}
                height={192}
                className="mx-auto h-full rounded-3xl object-cover drop-shadow-xl lg:mx-0 "
              />
            )}
            <h3 className="pb-2 pt-4 text-2xl font-bold leading-8 tracking-tight">{name}</h3>
            <div className="text-gray-500 dark:text-gray-400">{occupation}</div>
            <div className="text-gray-500 dark:text-gray-400">{company}</div>
            <div className="flex space-x-3 pt-6">
              <SocialIcon kind="mail" href={`mailto:${email}`} />
              <SocialIcon kind="github" href={github} />
              <SocialIcon kind="linkedin" href={linkedin} />
              <SocialIcon kind="x" href={twitter} />
              <SocialIcon kind="bluesky" href={bluesky} />
            </div>
          </div>
          <div className="prose max-w-none pb-8 pt-8 dark:prose-invert xl:col-span-2">
            {children}
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
