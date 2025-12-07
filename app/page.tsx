import { sortPosts, allCoreContent } from 'pliny/utils/contentlayer'
import { allEssays } from 'contentlayer/generated'
import Main from './Main'

import { getBooks, getProjects } from '@/lib/data'

export default async function Page() {
  const sortedPosts = sortPosts(allEssays)
  const posts = allCoreContent(sortedPosts)
  const books = await getBooks('curated')
  const projects = await getProjects()
  return <Main posts={posts} books={books} projects={projects} />
}
