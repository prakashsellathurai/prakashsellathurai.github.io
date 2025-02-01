import fetch from 'node-fetch'
import fs from 'fs'

const GITHUB_API_URL = 'https://api.github.com/users/prakashsellathurai/repos'

async function fetchRepos() {
  try {
    const response = await fetch(GITHUB_API_URL)
    const data = await response.json()

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
