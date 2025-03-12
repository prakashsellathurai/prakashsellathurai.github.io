import repos from './repos.json'
import leetcodesolutions from './leetcode-solutions.json'
interface Project {
  title: string
  description: string
  href?: string
  imgSrc?: string
  stars?: number
}

interface LeetcodeSolutions {
  title: string
  href: string
}

const projectsNamesToShowcase = [
  'keras',
  'pyqoi',
  'DeFIR',
  'CLothXMicroServices',
  'openpose-docker',
  'Heimdall',
]

const projectsData: Project[] = repos as Project[]
const sampleProjects: Project[] = projectsNamesToShowcase // preserve order of projectsNamesToShowcase
  .map((name) => projectsData.find((project) => project.title === name))
  .filter((project): project is Project => project !== undefined)
const leetcodeSolutions: LeetcodeSolutions[] = leetcodesolutions as LeetcodeSolutions[]

export { projectsData, sampleProjects, leetcodeSolutions }
