import { useEffect, useMemo, useRef, useState } from 'react'
import { apiRequest, normalizeCollection } from '../utils/apiClient.js'
import { useAuth } from '../state/AuthContext.jsx'

export default function useCourseData(courseId) {
  const { isAuthenticated } = useAuth()
  const [course, setCourse] = useState(null)
  const [sections, setSections] = useState([])
  const [enrollment, setEnrollment] = useState(null)
  const [lessonProgress, setLessonProgress] = useState({})
  const [categories, setCategories] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const [courseContent, categoriesData] = await Promise.all([
          apiRequest(`/courses/${courseId}/content`, { method: 'GET', auth: false }),
          apiRequest('/categories', { method: 'GET', auth: false }),
        ])

        if (!mounted) return

        const sectionsWithLessons = courseContent.sections || []
        setCourse(courseContent)
        setSections(sectionsWithLessons)
        setCategories(normalizeCollection(categoriesData))
        setStatus('ready')

        if (isAuthenticated) {
          try {
            const enrollmentData = await apiRequest(`/progress/enrollments/by-course/${courseId}`, {
              method: 'GET',
              auth: true,
            })
            if (mounted) setEnrollment(enrollmentData)
          } catch {
            if (mounted) setEnrollment(null)
          }

          try {
            const allLessonIds = sectionsWithLessons.flatMap((s) => s.lessons.map((l) => l.id))
            const progressEntries = {}

            if (allLessonIds.length > 0) {
              const batchResponse = await apiRequest(`/progress/lesson-progress/lessons/by-ids`, {
                method: 'POST',
                auth: true,
                body: { lesson_ids: allLessonIds },
                contentType: 'application/json',
              })

              batchResponse.found.forEach((p) => {
                progressEntries[p.lesson_id] = p
              })
            }

            if (mounted) setLessonProgress(progressEntries)
          } catch (err) {
            console.error('Ошибка загрузки прогресса:', err)
            if (mounted) setLessonProgress({})
          }
        } else if (mounted) {
          setEnrollment(null)
          setLessonProgress({})
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || 'Не удалось загрузить курс.')
          setStatus('error')
        }
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [courseId, isAuthenticated])

  const totalLessons = useMemo(
    () => sections.reduce((acc, section) => acc + section.lessons.length, 0),
    [sections],
  )

  const completedLessons = useMemo(
    () => Object.values(lessonProgress).filter((p) => p?.status === 'COMPLETED').length,
    [lessonProgress],
  )

  const progressPercent = totalLessons === 0 ? 0 : Math.round((completedLessons / totalLessons) * 100)

  const lastCompletedLessonId = useMemo(() => {
    return sections
      .flatMap((section) => section.lessons)
      .reduceRight((lastId, lesson) => {
        if (lastId) return lastId
        return lessonProgress[lesson.id]?.status === 'COMPLETED' ? lesson.id : null
      }, null)
  }, [sections, lessonProgress])

  // Обновление прогресса курса
  const lastSentRef = useRef({ course_id: null, total_lessons: 0, progress_percent: -1, last_lesson_id: null })
  useEffect(() => {
    lastSentRef.current = { course_id: null, total_lessons: 0, progress_percent: -1, last_lesson_id: null }
  }, [courseId])
  useEffect(() => {
    let mounted = true
    const upsert = async () => {
      if (!enrollment || totalLessons === 0) return
      const sent = lastSentRef.current
      const isSameCourse = sent.course_id === courseId
      if (
        isSameCourse &&
        sent.total_lessons === totalLessons &&
        sent.progress_percent === progressPercent &&
        sent.last_lesson_id === lastCompletedLessonId
      ) return
      sent.course_id = courseId
      sent.total_lessons = totalLessons
      sent.progress_percent = progressPercent
      sent.last_lesson_id = lastCompletedLessonId
      try {
        await apiRequest(`/progress/course-progress/courses/${courseId}`, {
          method: 'PUT',
          auth: true,
          body: {
            total_lessons: totalLessons,
            progress_percent: progressPercent,
            last_lesson_id: lastCompletedLessonId,
          },
        })
      } catch (err) {
        if (mounted) console.warn('Предупреждение при обновлении прогресса курса:', err)
      }
    }
    const timer = setTimeout(() => upsert(), 500)
    return () => {
      mounted = false
      clearTimeout(timer)
    }
  }, [courseId, enrollment, totalLessons, progressPercent, lastCompletedLessonId])

  // Автозавершение записи на курс
  useEffect(() => {
    let mounted = true
    const finalize = async () => {
      if (!enrollment || enrollment.status === 'COMPLETED') return
      if (progressPercent < 100) return
      try {
        const updated = await apiRequest(`/progress/enrollments/${enrollment.id}`, {
          method: 'PATCH',
          auth: true,
          body: { status: 'COMPLETED' },
        })
        if (mounted) setEnrollment(updated)
      } catch (err) {
        if (mounted) console.warn('Предупреждение при завершении курса:', err)
      }
    }
    finalize()
    return () => { mounted = false }
  }, [progressPercent, enrollment])

  return {
    course,
    setCourse,
    sections,
    setSections,
    enrollment,
    setEnrollment,
    lessonProgress,
    categories,
    status,
    error,
    totalLessons,
    progressPercent,
  }
}
