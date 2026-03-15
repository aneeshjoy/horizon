import { Routes, Route } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { VehiclePage } from './pages/VehiclePage'
import { ConfigurationPage } from './pages/ConfigurationPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ThemeProvider } from './components/theme/ThemeProvider'

function App() {
  return (
    <ThemeProvider defaultTheme="system">
      <div className="min-h-screen bg-background text-foreground">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/vehicle/:plate" element={<VehiclePage />} />
          <Route path="/config" element={<ConfigurationPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </ThemeProvider>
  )
}

export default App
