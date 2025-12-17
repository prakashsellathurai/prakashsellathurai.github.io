import { ReactNode } from 'react'

interface Props {
  children: ReactNode
}

export default function PageTitle({ children }: Props) {
  return (
    <h1 className="bg-gradient-to-r from-gray-900 via-primary-600 to-secondary-600 bg-clip-text text-3xl font-extrabold leading-9 tracking-tight text-transparent dark:from-gray-100 dark:via-primary-400 dark:to-secondary-400 sm:text-4xl sm:leading-10 md:text-5xl md:leading-14">
      {children}
    </h1>
  )
}
