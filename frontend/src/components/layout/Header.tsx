import { Link } from 'react-router-dom'
import { Car, Settings } from 'lucide-react'
import { ThemeToggle } from '@/components/theme/ThemeToggle'
import { useTheme } from '@/components/theme/ThemeProvider'

export function Header() {
  const { actualTheme } = useTheme()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex h-16 items-center">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2 font-semibold">
            <Car className="h-6 w-6" />
            <span className="hidden sm:inline-block">Horizon</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm">
            <Link
              to="/"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Search
            </Link>
          </nav>
        </div>

        <div className="ml-auto flex items-center gap-4">
          <Link
            to="/config"
            className="hidden sm:flex items-center gap-2 text-sm transition-colors hover:text-foreground/80 text-foreground/60"
          >
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </Link>

          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
