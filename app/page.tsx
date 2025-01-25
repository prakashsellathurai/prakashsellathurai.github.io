import { sortPosts, allCoreContent } from 'pliny/utils/contentlayer'
import { allEssays } from 'contentlayer/generated'
import Main from './Main'

export default async function Page() {
  const sortedPosts = sortPosts(allEssays)
  const posts = allCoreContent(sortedPosts)
  return <Main posts={posts} />
}
