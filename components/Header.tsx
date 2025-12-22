import siteMetadata from '@/data/siteMetadata'
import headerNavLinks from '@/data/headerNavLinks'
import Link from './Link'
import MobileNav from './MobileNav'
import SearchButton from './SearchButton'

const Header = () => {
  return (
    <header className="relative z-50 mb-6 w-full">
      {/* Structural Line / HUD top border - Neutral Primary */}
      <div className="pointer-events-none absolute -top-4 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary-500/30 to-transparent opacity-70" />

      {/* Main Header Container - Glassy and Technical - Neutral Refresh */}
      <div className="glass-panel-enhanced relative flex items-center justify-between rounded-none border-x-0 border-b border-t-0 border-b-black/5 px-4 py-4 backdrop-blur-xl dark:border-b-white/5 sm:rounded-2xl sm:border sm:px-8">
        {/* Technical Corner Markers (Decorative) - Neutral Secondary */}
        <div className="pointer-events-none absolute -left-1 -top-1 h-3 w-3 border-l-2 border-t-2 border-primary-400/30" />
        <div className="pointer-events-none absolute -right-1 -top-1 h-3 w-3 border-r-2 border-t-2 border-primary-400/30" />
        <div className="pointer-events-none absolute -bottom-1 -left-1 h-3 w-3 border-b-2 border-l-2 border-primary-400/30" />
        <div className="pointer-events-none absolute -bottom-1 -right-1 h-3 w-3 border-b-2 border-r-2 border-primary-400/30" />

        <Link
          href="/"
          aria-label={siteMetadata.headerTitle}
          className="group relative flex items-center gap-3 overflow-hidden rounded-md px-2 py-1 transition-all hover:bg-primary-500/10"
        >
          {/* Logo Animation / Tech Effect */}

          <div className="hidden flex-col sm:flex">
            <span className="text-lg font-bold tracking-tight text-gray-900 dark:text-gray-100">
              {siteMetadata.siteHome}
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <div className="flex items-center gap-6">
          <div className="hidden items-center gap-1 sm:flex">
            {headerNavLinks
              .filter((link) => link.href !== '/')
              .map((link) => (
                <Link
                  key={link.title}
                  href={link.href}
                  className="group relative px-4 py-2 font-mono text-sm font-medium text-gray-600 transition-colors hover:text-primary-600 dark:text-gray-300 dark:hover:text-primary-400"
                >
                  {/* Hover Bracket Effect */}
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 text-primary-500 opacity-0 transition-opacity group-hover:opacity-100">
                    [
                  </span>
                  <span className="relative z-10">{link.title}</span>
                  <span className="absolute right-0 top-1/2 -translate-y-1/2 text-primary-500 opacity-0 transition-opacity group-hover:opacity-100">
                    ]
                  </span>

                  {/* Subtle background glow on hover */}
                  <div className="absolute inset-0 -z-10 mx-2 rounded bg-primary-500/0 transition-colors group-hover:bg-primary-500/5" />
                </Link>
              ))}
          </div>

          {/* Utilities (Search, Theme, Mobile Menu) */}
          <div className="flex items-center gap-3 border-l border-gray-200 pl-4 dark:border-gray-700">
            <SearchButton />
            <MobileNav />
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
