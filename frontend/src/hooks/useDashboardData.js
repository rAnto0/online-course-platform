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
        const courseIds = safeEnrollments.map(e => e.course_id)
        const batch = await apiRequest('/courses/by-ids', {
          method: 'POST',
          body: { course_ids: courseIds },
        })
        const coursesMap = new Map(batch.found.map(c => [c.id, c]))
        const enriched = safeEnrollments.map(enrollment => ({
          ...enrollment,
          course: coursesMap.get(enrollment.course_id) || null,
          courseError: coursesMap.has(enrollment.course_id) ? null : 'Курс удален или скрыт',
        }))
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
