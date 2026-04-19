import { useEffect, useState } from 'react'
import { apiRequest, normalizeCollection } from '../utils/apiClient.js'
import { useAuth } from '../state/AuthContext.jsx'

export default function useDashboardData() {
  const { user: currentUser, refreshSession } = useAuth()
  const [courses, setCourses] = useState([])
  const [categories, setCategories] = useState([])
  const [enrollments, setEnrollments] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const [coursesData, categoriesData] = await Promise.all([
          apiRequest('/courses?skip=0&limit=10000', { method: 'GET', auth: false }),
          apiRequest('/categories', { method: 'GET', auth: false }),
        ])

        if (mounted) {
          setCourses(normalizeCollection(coursesData))
          setCategories(normalizeCollection(categoriesData))
        }

        if (!currentUser?.id) return

        const enrollmentsData = await apiRequest('/progress/enrollments/by-user', {
          method: 'GET',
          auth: true,
        })
        const safeEnrollments = normalizeCollection(enrollmentsData)
        const enriched = await Promise.all(
          safeEnrollments.map(async (enrollment) => {
            try {
              const course = await apiRequest(`/courses/${enrollment.course_id}`, {
                method: 'GET',
                auth: false,
              })
              return { ...enrollment, course, courseError: null }
            } catch (enrollError) {
              const message = enrollError?.status === 404
                ? 'Курс удален или скрыт'
                : 'Курс временно недоступен'
              return { ...enrollment, course: null, courseError: message }
            }
          }),
        )
        if (mounted) {
          setEnrollments(enriched)
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || 'Не удалось загрузить данные кабинета.')
        }
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [currentUser])

  return {
    user: currentUser,
    courses,
    categories,
    setCategories,
    enrollments,
    error,
    refreshSession,
  }
}
