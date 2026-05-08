import { execSync } from 'child_process'
import fetch from 'node-fetch'
import fs from 'fs'
const GITHUB_API_URL = 'https://api.github.com/users/prakashsellathurai/repos?per_page=100'
const GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'
function getGitHubToken() {
  if (process.env.GITHUB_TOKEN) {
    return process.env.GITHUB_TOKEN
  }
  try {
    return execSync('gh auth token', { encoding: 'utf-8' }).trim()
  } catch {
    return ''
  }
}
const GITHUB_TOKEN = getGitHubToken()
async function fetchAllRepos(url) {
  let repos = []
  let nextUrl = url
  while (nextUrl) {
    const response = await fetch(nextUrl)
    const data = await response.json()
    repos = repos.concat(data)
    const linkHeader = response.headers.get('link')
    if (linkHeader) {
      const links = linkHeader.split(',').reduce((acc, link) => {
        const match = link.match(/<([^>]+)>;\s*rel="([^"]+)"/)
        if (match) {
          acc[match[2]] = match[1]
        }
        return acc
      }, {})
      nextUrl = links.next
    } else {
      nextUrl = null
    }
  }
  return repos
}
async function fetchPinnedRepos() {
  if (!GITHUB_TOKEN) {
    console.log('No GITHUB_TOKEN env var, skipping pinned repos')
    return []
  }
  const query = `
    query {
      user(login: "prakashsellathurai") {
        pinnedItems(first: 6, types: REPOSITORY) {
          nodes {
            ... on Repository {
              name
              description
            }
          }
        }
      }
    }
  `
  const response = await fetch(GITHUB_GRAPHQL_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${GITHUB_TOKEN}`,
    },
    body: JSON.stringify({ query }),
  })
  const result = await response.json()
  const pinned = result.data?.user?.pinnedItems?.nodes || []
  return pinned.map((repo) => ({
    name: repo.name,
    description: repo.description,
  }))
}
async function fetchRepos() {
  try {
    const [allRepos, pinnedRepos] = await Promise.all([
      fetchAllRepos(GITHUB_API_URL),
      fetchPinnedRepos(),
    ])
    allRepos.sort((a, b) => new Date(b.pushed_at) - new Date(a.pushed_at))
    const pinnedNames = new Set(pinnedRepos.map((p) => p.name))
    const reposWithPinned = allRepos.map((repo) => {
      const pinned = pinnedNames.has(repo.name)
      return {
        title: repo.name,
        href: repo.html_url,
        website: repo.homepage,
        description: repo.description,
        stars: repo.stargazers_count,
        pinned: pinned || false,
      }
    })
    const pinnedFirst = reposWithPinned.filter((r) => r.pinned)
    const rest = reposWithPinned.filter((r) => !r.pinned)
    const finalData = [...pinnedFirst, ...rest]
    // Save json data to a file
    fs.writeFileSync('./data/repos.json', JSON.stringify(finalData, null, 4), 'utf-8')
    console.log(`Updated repos.json with ${finalData.length} repos (${pinnedFirst.length} pinned)`)
  } catch (error) {
    console.error('Error fetching GitHub repositories:', error)
  }
}
async function listSubtree(githubrepo, path, ref = 'main') {
  const url = `https://api.github.com/repos/${githubrepo}/git/trees/${ref}?recursive=1`
  const response = await fetch(url)
  const data = await response.json()
  const files = data.tree
    .filter((file) => file.type === 'blob' && file.path.startsWith(path))
    .map((file) => file.path)
  return files
}
async function writeleetcodeSolutionsAsJson() {
  const files = await listSubtree('prakashsellathurai/leetcode-solutions', 'problems', 'gh-pages')
  const yamldata = files.map((file) => ({
    title: file,
    href: `leetcode-solutions/${file}`,
  }))
  fs.writeFileSync('./data/leetcode-solutions.json', JSON.stringify(yamldata, null, 4), 'utf-8')
}
fetchRepos()
writeleetcodeSolutionsAsJson()