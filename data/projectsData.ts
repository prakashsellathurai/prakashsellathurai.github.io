import repos from './repos.json'
interface Project {
  title: string
  description: string
  href?: string
  imgSrc?: string
}

const projectsData: Project[] = repos as Project[]
const sampleProjects: Project[] = repos.slice(0, 6) as Project[]

export { projectsData, sampleProjects }
