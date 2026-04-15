import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { useEffect, lazy, Suspense } from 'react'
import { createUser } from './api/client'
import Home from './pages/Home'
import IssuePage from './pages/IssuePage'
import SubmitPage from './pages/SubmitPage'

// SurveyPage is owned by Person C — stub in pages/SurveyPage.jsx
const SurveyPage = lazy(() => import('./pages/SurveyPage.jsx'))

function NavBar() {
  return (
    <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="text-white font-bold text-lg tracking-tight hover:text-indigo-300 transition-colors">
          Campus Pulse
        </Link>
        <Link
          to="/submit"
          className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          Share your view
        </Link>
      </div>
    </nav>
  )
}

export default function App() {
  useEffect(() => {
    if (!localStorage.getItem('user_id')) {
      createUser()
        .then(data => localStorage.setItem('user_id', data.id))
        .catch(() => {})
    }
  }, [])

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-900">
        <NavBar />
        <Suspense fallback={null}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/issue/:id" element={<IssuePage />} />
            <Route path="/issue/:id/survey" element={<SurveyPage />} />
            <Route path="/submit" element={<SubmitPage />} />
          </Routes>
        </Suspense>
      </div>
    </BrowserRouter>
  )
}
