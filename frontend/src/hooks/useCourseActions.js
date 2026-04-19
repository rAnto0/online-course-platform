import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../utils/apiClient.js'

export default function useCourseActions(courseId) {
  const navigate = useNavigate()
  const [sectionError, setSectionError] = useState('')
  const [lessonError, setLessonError] = useState('')

  const enroll = useCallback(async () => {
    try {
      const data = await apiRequest('/progress/enrollments', {
        method: 'POST',
        auth: true,
        body: { course_id: courseId },
      })
      return data
    } catch {
      return null
    }
  }, [courseId])

  const publishCourse = useCallback(async () => {
    try {
      const updated = await apiRequest(`/courses/${courseId}/publish`, { method: 'PATCH', auth: true })
      return updated
    } catch (err) {
      setSectionError(err.message || 'Не удалось опубликовать курс.')
      return null
    }
  }, [courseId])

  const archiveCourse = useCallback(async () => {
    try {
      const updated = await apiRequest(`/courses/${courseId}/archive`, { method: 'PATCH', auth: true })
      return updated
    } catch (err) {
      setSectionError(err.message || 'Не удалось архивировать курс.')
      return null
    }
  }, [courseId])

  const deleteCourse = useCallback(async () => {
    try {
      await apiRequest(`/courses/${courseId}`, { method: 'DELETE', auth: true })
      navigate('/')
      return true
    } catch (err) {
      setSectionError(err.message || 'Не удалось удалить курс.')
      return false
    }
  }, [courseId, navigate])

  const updateCourse = useCallback(async (payload) => {
    try {
      const updated = await apiRequest(`/courses/${courseId}`, {
        method: 'PUT',
        auth: true,
        body: payload,
      })
      return updated
    } catch (err) {
      setSectionError(err.message || 'Не удалось обновить курс.')
      return null
    }
  }, [courseId])

  const addSection = useCallback(async (title) => {
    setSectionError('')
    try {
      const created = await apiRequest(`/courses/${courseId}/sections`, {
        method: 'POST',
        auth: true,
        body: { title },
      })
      return created
    } catch (err) {
      setSectionError(err.message || 'Не удалось добавить секцию.')
      return null
    }
  }, [courseId])

  const updateSection = useCallback(async (sectionId, title) => {
    setSectionError('')
    try {
      const updated = await apiRequest(`/courses/${courseId}/sections/${sectionId}`, {
        method: 'PUT',
        auth: true,
        body: { title },
      })
      return updated
    } catch (err) {
      setSectionError(err.message || 'Не удалось обновить секцию.')
      return null
    }
  }, [courseId])

  const deleteSection = useCallback(async (sectionId) => {
    setSectionError('')
    try {
      await apiRequest(`/courses/${courseId}/sections/${sectionId}`, { method: 'DELETE', auth: true })
      return true
    } catch (err) {
      setSectionError(err.message || 'Не удалось удалить секцию.')
      return false
    }
  }, [courseId])

  const addLesson = useCallback(async (sectionId, form) => {
    setLessonError('')
    try {
      const created = await apiRequest(`/courses/${courseId}/sections/${sectionId}/lessons`, {
        method: 'POST',
        auth: true,
        body: {
          title: form.title,
          content: form.content || null,
          lesson_type: form.lesson_type || null,
          video_url: form.video_url || null,
          duration: form.duration ? Number(form.duration) : null,
        },
      })
      return created
    } catch (err) {
      setLessonError(err.message || 'Не удалось добавить урок.')
      return null
    }
  }, [courseId])

  const updateLesson = useCallback(async (sectionId, lessonId, form) => {
    setLessonError('')
    try {
      const updated = await apiRequest(
        `/courses/${courseId}/sections/${sectionId}/lessons/${lessonId}`,
        {
          method: 'PUT',
          auth: true,
          body: {
            title: form.title,
            content: form.content || null,
            lesson_type: form.lesson_type || null,
            video_url: form.video_url || null,
            duration: form.duration ? Number(form.duration) : null,
          },
        }
      )
      return updated
    } catch (err) {
      setLessonError(err.message || 'Не удалось обновить урок.')
      return null
    }
  }, [courseId])

  const deleteLesson = useCallback(async (sectionId, lessonId) => {
    setLessonError('')
    try {
      await apiRequest(`/courses/${courseId}/sections/${sectionId}/lessons/${lessonId}`, {
        method: 'DELETE',
        auth: true,
      })
      return true
    } catch (err) {
      setLessonError(err.message || 'Не удалось удалить урок.')
      return false
    }
  }, [courseId])

  return {
    sectionError,
    lessonError,
    enroll,
    publishCourse,
    archiveCourse,
    deleteCourse,
    updateCourse,
    addSection,
    updateSection,
    deleteSection,
    addLesson,
    updateLesson,
    deleteLesson,
  }
}
