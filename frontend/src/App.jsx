import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import TopBar from './components/TopBar.jsx'
import Footer from './components/Footer.jsx'
import AssistantChatWidget from './components/AssistantChatWidget.jsx'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Dashboard from './pages/Dashboard.jsx'
import CourseDetails from './pages/CourseDetails.jsx'
import LessonViewer from './pages/LessonViewer.jsx'
import Profile from './pages/Profile.jsx'
import NotFound from './pages/NotFound.jsx'
import { useAuth } from './state/AuthContext.jsx'

function App() {
  const { status, isAuthenticated } = useAuth()

  if (status === 'loading') {
    return (
      <div className="app-shell">
        <div className="empty">Загрузка профиля...</div>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <TopBar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/courses/:courseId" element={<CourseDetails />} />
          <Route path="/courses/:courseId/sections/:sectionId/lessons/:lessonId" element={<LessonViewer />} />
          <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />} />
          <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Register />} />
          <Route path="/dashboard" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
          <Route path="/profile" element={isAuthenticated ? <Profile /> : <Navigate to="/login" />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <AssistantChatWidget />
      <Footer />
    </div>
  )
}

export default App
