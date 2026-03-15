import { type ReactNode, createContext, useContext, useEffect, useState } from 'react'

type Theme = 'dark' | 'light' | 'system'

interface ThemeContextType {
  theme: Theme
  actualTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

interface ThemeProviderProps {
  children: ReactNode
  defaultTheme?: Theme
}

export function ThemeProvider({ children, defaultTheme = 'system' }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(defaultTheme)
  const [actualTheme, setActualTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const root = document.documentElement
    const storedTheme = localStorage.getItem('theme') as Theme || defaultTheme

    setThemeState(storedTheme)

    const updateTheme = () => {
      const isDark = storedTheme === 'dark' ||
        (storedTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

      root.classList.remove('light', 'dark')
      root.classList.add(isDark ? 'dark' : 'light')
      setActualTheme(isDark ? 'dark' : 'light')
    }

    updateTheme()

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      if (storedTheme === 'system') {
        updateTheme()
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [defaultTheme])

  const setTheme = (newTheme: Theme) => {
    const root = document.documentElement
    localStorage.setItem('theme', newTheme)
    setThemeState(newTheme)

    const isDark = newTheme === 'dark' ||
      (newTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

    root.classList.remove('light', 'dark')
    root.classList.add(isDark ? 'dark' : 'light')
    setActualTheme(isDark ? 'dark' : 'light')
  }

  return (
    <ThemeContext.Provider value={{ theme, actualTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
