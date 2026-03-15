import { useEffect, useState } from 'react'

export type Theme = 'dark' | 'light' | 'system'

export function useTheme() {
  const [theme, setTheme] = useState<Theme>('system')
  const [actualTheme, setActualTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const root = window.document.documentElement
    const storedTheme = localStorage.getItem('theme') as Theme || 'system'

    setTheme(storedTheme)

    const updateTheme = () => {
      const isDark = storedTheme === 'dark' ||
        (storedTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

      root.classList.remove('light', 'dark')
      root.classList.add(isDark ? 'dark' : 'light')
      setActualTheme(isDark ? 'dark' : 'light')
    }

    updateTheme()

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      if (storedTheme === 'system') {
        updateTheme()
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  const changeTheme = (newTheme: Theme) => {
    const root = window.document.documentElement
    localStorage.setItem('theme', newTheme)
    setTheme(newTheme)

    const isDark = newTheme === 'dark' ||
      (newTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

    root.classList.remove('light', 'dark')
    root.classList.add(isDark ? 'dark' : 'light')
    setActualTheme(isDark ? 'dark' : 'light')
  }

  return {
    theme,
    actualTheme,
    setTheme: changeTheme,
  }
}
