import fetch from 'node-fetch'
import fs from 'fs'

const GITHUB_API_URL = 'https://api.github.com/users/prakashsellathurai/repos?per_page=100'

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

async function fetchRepos() {
  try {
    const data = await fetchAllRepos(GITHUB_API_URL)

    // Sort data by 'pushed_at' in descending order
    data.sort((a, b) => new Date(b.pushed_at) - new Date(a.pushed_at))

    // Prepare YAML data
    const yamldata = data.map((datum) => ({
      title: datum.name,
      href: datum.html_url,
      description: datum.description,
    }))

    // Save json data to a file
    fs.writeFileSync('./data/repos.json', JSON.stringify(yamldata, null, 4), 'utf-8')
  } catch (error) {
    console.error('Error fetching GitHub repositories:', error)
  }
}

fetchRepos()
