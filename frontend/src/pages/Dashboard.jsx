import { useMemo, useState } from 'react'
import useDashboardData from '../hooks/useDashboardData.js'
import CourseList from '../components/dashboard/CourseList.jsx'
import EnrollmentList from '../components/dashboard/EnrollmentList.jsx'
import CreateCourseModal from '../components/dashboard/CreateCourseModal.jsx'
import CategoryManager from '../components/dashboard/CategoryManager.jsx'

export default function Dashboard() {
  const {
    user,
    courses,
    categories,
    enrollments,
    error,
    refreshSession,
    setCategories,
  } = useDashboardData()

  const [localCourses, setLocalCourses] = useState([])
  const displayCourses = useMemo(() => {
    if (localCourses.length === 0) return courses
    const localIds = new Set(localCourses.map((course) => course.id))
    return [...localCourses, ...courses.filter((course) => !localIds.has(course.id))]
  }, [localCourses, courses])
  const [showCreateModal, setShowCreateModal] = useState(false)

  if (!user) {
    return (
      <div className="page">
        <div className="empty">Загрузка...</div>
      </div>
    )
  }

  return (
    <div className="page">
      <section className="section">
        <div className="section__header">
          <div>
            <h2>Кабинет</h2>
            <p>Управляйте курсами, категориями и своим обучением.</p>
          </div>
        </div>
        {error && <div className="form-error">{error}</div>}
      </section>

      <CourseList
        courses={displayCourses}
        user={user}
        onCreateClick={() => setShowCreateModal(true)}
      />

      <EnrollmentList enrollments={enrollments} />

      {user.role === 'admin' && <CategoryManager categories={categories} setCategories={setCategories} />}

      {showCreateModal && (
        <CreateCourseModal
          categories={categories}
          onClose={() => setShowCreateModal(false)}
          onCreated={(newCourse) => setLocalCourses((prev) => [newCourse, ...prev])}
          refreshSession={refreshSession}
        />
      )}
    </div>
  )
}
