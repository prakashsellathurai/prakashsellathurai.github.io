import repos from './repos.json'
interface Project {
  title: string
  description: string
  href?: string
  imgSrc?: string
  stars?: number
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

export { projectsData, sampleProjects }
