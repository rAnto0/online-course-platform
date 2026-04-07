import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiRequest } from '../utils/apiClient.js'
import { lessonTypeLabels } from '../utils/format.js'
import { renderMarkdown } from '../utils/markdown.js'
import { useAuth } from '../state/AuthContext.jsx'

export default function LessonViewer() {
  const { courseId, sectionId, lessonId } = useParams()
  const { isAuthenticated } = useAuth()
  const [lesson, setLesson] = useState(null)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [hasCompleted, setHasCompleted] = useState(false)
  const [isTracking, setIsTracking] = useState(false)
  const contentRef = useRef(null)

  const fetchLesson = useCallback(async () => {
    const data = await apiRequest(`/courses/${courseId}/sections/${sectionId}/lessons/${lessonId}`, {
      method: 'GET',
      auth: false,
    })
    setLesson(data)
  }, [courseId, sectionId, lessonId])

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        await fetchLesson()
        if (mounted) {
          setStatus('ready')
        }
        if (isAuthenticated) {
          try {
            await apiRequest(`/progress/enrollments/by-course/${courseId}`, {
              method: 'GET',
              auth: true,
            })
            setIsTracking(true)
            await apiRequest(`/progress/lesson-progress/lessons/${lessonId}`, {
              method: 'PUT',
              auth: true,
              body: {
                course_id: courseId,
                section_id: sectionId,
                status: 'IN_PROGRESS',
                progress_percent: 20,
              },
            })
          } catch (err) {
            setIsTracking(false)
          }
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || 'Не удалось загрузить урок.')
          setStatus('error')
        }
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [courseId, sectionId, lessonId, isAuthenticated, fetchLesson])

  const markCompleted = useCallback(async () => {
    if (!isAuthenticated || hasCompleted) return
    setHasCompleted(true)
    try {
      await apiRequest(`/progress/lesson-progress/lessons/${lessonId}`, {
        method: 'PUT',
        auth: true,
        body: {
          course_id: courseId,
          section_id: sectionId,
          status: 'COMPLETED',
          progress_percent: 100,
        },
      })
    } catch (err) {
      console.warn('Lesson completion warning:', err)
    }
  }, [courseId, sectionId, lessonId, isAuthenticated, hasCompleted])

  const handleScroll = useCallback(() => {
    if (!contentRef.current || hasCompleted) return
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement
    if (scrollTop + clientHeight >= scrollHeight - 40) {
      markCompleted()
    }
  }, [hasCompleted, markCompleted])

  useEffect(() => {
    if (!isTracking) return undefined
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [handleScroll, isTracking])

  useEffect(() => {
    if (!isTracking) return undefined
    const checkCompletion = () => {
      const { scrollHeight, clientHeight } = document.documentElement
      if (scrollHeight <= clientHeight + 40) {
        markCompleted()
      }
    }
    const timer = setTimeout(checkCompletion, 200)
    return () => clearTimeout(timer)
  }, [isTracking, markCompleted, lessonId])

  const lessonMeta = useMemo(() => {
    if (!lesson) return ''
    const parts = [lessonTypeLabels[lesson.lesson_type] || lesson.lesson_type]
    if (lesson.duration) {
      parts.push(`${lesson.duration} мин`)
    }
    return parts.join(' · ')
  }, [lesson])

  if (status === 'loading') {
    return <div className="page"><div className="empty">Загрузка урока...</div></div>
  }

  if (status === 'error') {
    return <div className="page"><div className="empty">{error}</div></div>
  }

  return (
    <div className="page lesson-page" ref={contentRef}>
      <Link className="link-back" to={`/courses/${courseId}`}>← Назад к курсу</Link>
      <div className="lesson-header">
        <h2>{lesson.title}</h2>
        <div className="lesson-meta">{lessonMeta}</div>
        {!isAuthenticated && (
          <div className="form-error">Войдите, чтобы отмечать прогресс.</div>
        )}
        {hasCompleted && (
          <div className="pill">Урок завершен</div>
        )}
      </div>
      <div className="lesson-content">
        {lesson.video_url && (
          <a className="link" href={lesson.video_url} target="_blank" rel="noreferrer">
            Смотреть видео
          </a>
        )}
        <div
          className="lesson-text markdown"
          dangerouslySetInnerHTML={{
            __html: renderMarkdown(lesson.content || 'Контент урока еще не заполнен.'),
          }}
        />
      </div>
      <div className="lesson-footer">
        <p>Доскролльте до конца страницы, чтобы отметить урок как пройденный.</p>
      </div>
    </div>
  )
}
