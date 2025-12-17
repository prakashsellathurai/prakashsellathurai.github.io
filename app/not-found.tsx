import Link from '@/components/Link'

export default function NotFound() {
  return (
    <div className="glass-panel-enhanced my-8 flex flex-col items-center justify-center rounded-3xl p-12 text-center md:p-16">
      <div className="space-x-2 pb-8 pt-6 md:space-y-5">
        <h1 className="bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-6xl font-extrabold leading-9 tracking-tight text-transparent md:text-8xl md:leading-14">
          404
        </h1>
      </div>
      <div className="max-w-md">
        <p className="mb-4 text-xl font-bold leading-normal text-gray-900 dark:text-gray-100 md:text-2xl">
          Sorry we couldn't find this page.
        </p>
        <p className="mb-8 text-gray-600 dark:text-gray-400">
          But don't worry, you can find plenty of other things on our homepage.
        </p>
        <Link
          href="/"
          className="group inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-primary-500 to-secondary-500 px-8 py-3 text-base font-bold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-2xl focus:outline-none"
        >
          Back to homepage
        </Link>
      </div>
    </div>
  )
}
