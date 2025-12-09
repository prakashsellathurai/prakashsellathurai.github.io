import siteMetadata from '@/data/siteMetadata'
import headerNavLinks from '@/data/headerNavLinks'
import Link from './Link'
import MobileNav from './MobileNav'
import SearchButton from './SearchButton'

const Header = () => {
  let headerClass = 'relative z-50 w-full mb-6'
  if (siteMetadata.stickyNav) {
    headerClass += ' sticky top-0 backdrop-blur-sm bg-white/70 dark:bg-slate-900/70'
  }

  return (
    <header className={headerClass}>
      {/* Tech/Blueprint Deco Line */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent opacity-50 dark:via-gray-700" />

      <div className="flex items-center justify-between py-5">
        <Link
          href="/"
          aria-label={siteMetadata.headerTitle}
          className="group flex items-center gap-2"
        >
          <div className="relative flex items-center px-3 py-1">
            {/* Redline Layout - Logo */}
            <div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
              <div className="absolute inset-0 border border-dashed border-primary-500/40" />
              <div className="absolute left-0 top-0 h-1.5 w-1.5 border-l-2 border-t-2 border-primary-500" />
              <div className="absolute right-0 top-0 h-1.5 w-1.5 border-r-2 border-t-2 border-primary-500" />
              <div className="absolute bottom-0 left-0 h-1.5 w-1.5 border-b-2 border-l-2 border-primary-500" />
              <div className="absolute bottom-0 right-0 h-1.5 w-1.5 border-b-2 border-r-2 border-primary-500" />
            </div>

            <div className="text-xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
              {siteMetadata.siteHome}
            </div>
          </div>
        </Link>

        <div className="flex items-center gap-6">
          <div className="hidden items-center gap-1 sm:flex">
            {headerNavLinks
              .filter((link) => link.href !== '/')
              .map((link) => (
                <Link
                  key={link.title}
                  href={link.href}
                  className="group relative px-3 py-1 text-sm font-medium text-gray-600 transition-colors hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400"
                >
                  {/* Redline Layout - Nav Links */}
                  <div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                    <div className="absolute inset-0 border border-dashed border-primary-500/40" />
                    <div className="absolute left-0 top-0 h-1.5 w-1.5 border-l-2 border-t-2 border-primary-500" />
                    <div className="absolute right-0 top-0 h-1.5 w-1.5 border-r-2 border-t-2 border-primary-500" />
                    <div className="absolute bottom-0 left-0 h-1.5 w-1.5 border-b-2 border-l-2 border-primary-500" />
                    <div className="absolute bottom-0 right-0 h-1.5 w-1.5 border-b-2 border-r-2 border-primary-500" />
                  </div>

                  <span className="relative block">{link.title}</span>
                </Link>
              ))}
          </div>

          <div className="flex items-center gap-2 pl-2 sm:border-l sm:border-gray-200 sm:pl-4 dark:sm:border-gray-800">
            <SearchButton />
            <MobileNav />
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
