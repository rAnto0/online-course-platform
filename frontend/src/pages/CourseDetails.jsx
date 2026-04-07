import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiRequest, normalizeCollection } from '../utils/apiClient.js'
import {
  enrollmentStatusLabels,
  formatPrice,
  lessonProgressLabels,
  lessonTypeLabels,
  levelLabels,
} from '../utils/format.js'
import { markdownToText, renderMarkdown } from '../utils/markdown.js'
import { useAuth } from '../state/AuthContext.jsx'

export default function CourseDetails() {
  const { courseId } = useParams()
  const { user, isAuthenticated } = useAuth()
  const [course, setCourse] = useState(null)
  const [sections, setSections] = useState([])
  const [enrollment, setEnrollment] = useState(null)
  const [lessonProgress, setLessonProgress] = useState({})
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [sectionError, setSectionError] = useState('')
  const [lessonError, setLessonError] = useState('')
  const [showFullDescription, setShowFullDescription] = useState(false)
  const [showEditCourse, setShowEditCourse] = useState(false)
  const [editCourseForm, setEditCourseForm] = useState({
    title: '',
    description: '',
    category_id: '',
    level: '',
    price: '',
    thumbnail_url: '',
  })
  const [categories, setCategories] = useState([])
  const [newSectionTitle, setNewSectionTitle] = useState('')
  const [newLesson, setNewLesson] = useState({})
  const [editingSectionId, setEditingSectionId] = useState(null)
  const [editingSectionTitle, setEditingSectionTitle] = useState('')
  const [editingLessonId, setEditingLessonId] = useState(null)
  const [editingLessonForm, setEditingLessonForm] = useState({})

  const isOwner = Boolean(user && course && user.id === course.author_id)
  const canManageCourse = Boolean(user && course && (user.role === 'admin' || isOwner))

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const courseData = await apiRequest(`/courses/${courseId}`, { method: 'GET', auth: false })
        const sectionsData = await apiRequest(`/courses/${courseId}/sections`, {
          method: 'GET',
          auth: false,
        })

        const sectionsWithLessons = await Promise.all(
          normalizeCollection(sectionsData).map(async (section) => {
            const lessons = await apiRequest(`/courses/${courseId}/sections/${section.id}/lessons`, {
              method: 'GET',
              auth: false,
            })
            return { ...section, lessons: normalizeCollection(lessons) }
          }),
        )

        if (!mounted) return
        setCourse(courseData)
        setEditCourseForm({
          title: courseData.title || '',
          description: courseData.description || '',
          category_id: courseData.category_id || '',
          level: courseData.level || '',
          price: courseData.price ?? '',
          thumbnail_url: courseData.thumbnail_url || '',
        })
        setSections(sectionsWithLessons)
        setStatus('ready')

        if (isAuthenticated) {
          try {
            const enrollmentData = await apiRequest(`/progress/enrollments/by-course/${courseId}`, {
              method: 'GET',
              auth: true,
            })
            setEnrollment(enrollmentData)
          } catch (err) {
            setEnrollment(null)
          }

          const progressEntries = {}
          await Promise.all(
            sectionsWithLessons.flatMap((section) =>
              section.lessons.map(async (lesson) => {
                try {
                  const lessonProgressData = await apiRequest(
                    `/progress/lesson-progress/lessons/${lesson.id}`,
                    { method: 'GET', auth: true },
                  )
                  progressEntries[lesson.id] = lessonProgressData
                } catch (err) {
                  progressEntries[lesson.id] = null
                }
              }),
            ),
          )
          if (mounted) {
            setLessonProgress(progressEntries)
          }
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

  useEffect(() => {
    let mounted = true
    if (!canManageCourse) return () => {}
    const loadCategories = async () => {
      try {
        const categoriesData = await apiRequest('/categories', { method: 'GET', auth: false })
        if (mounted) {
          setCategories(normalizeCollection(categoriesData))
        }
      } catch (err) {
        if (mounted) {
          setCategories([])
        }
      }
    }
    loadCategories()
    return () => {
      mounted = false
    }
  }, [canManageCourse])

  const totalLessons = useMemo(
    () => sections.reduce((acc, section) => acc + section.lessons.length, 0),
    [sections],
  )

  const completedLessons = useMemo(() => {
    return Object.values(lessonProgress).filter((progress) => progress?.status === 'COMPLETED').length
  }, [lessonProgress])

  const progressPercent = totalLessons === 0 ? 0 : Math.round((completedLessons / totalLessons) * 100)
  const lastCompletedLessonId = useMemo(() => {
    let lastId = null
    sections.forEach((section) => {
      section.lessons.forEach((lesson) => {
        if (lessonProgress[lesson.id]?.status === 'COMPLETED') {
          lastId = lesson.id
        }
      })
    })
    return lastId
  }, [sections, lessonProgress])

  useEffect(() => {
    const upsertCourseProgress = async () => {
      if (!enrollment) return
      if (totalLessons === 0) return
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
        console.warn('Course progress upsert warning:', err)
      }
    }
    upsertCourseProgress()
  }, [courseId, enrollment, totalLessons, progressPercent, lastCompletedLessonId])

  useEffect(() => {
    const finalizeCourse = async () => {
      if (!enrollment || enrollment.status === 'COMPLETED') return
      if (progressPercent < 100) return
      try {
        const updated = await apiRequest(`/progress/enrollments/${enrollment.id}`, {
          method: 'PATCH',
          auth: true,
          body: { status: 'COMPLETED' },
        })
        setEnrollment(updated)
      } catch (err) {
        console.warn('Course completion warning:', err)
      }
    }
    finalizeCourse()
  }, [progressPercent, enrollment])

  const enroll = async () => {
    try {
      const data = await apiRequest('/progress/enrollments', {
        method: 'POST',
        auth: true,
        body: { course_id: courseId },
      })
      setEnrollment(data)
    } catch (err) {
      setError(err.message || 'Не удалось записаться на курс.')
    }
  }

  const publishCourse = async () => {
    try {
      const updated = await apiRequest(`/courses/${courseId}/publish`, { method: 'PATCH', auth: true })
      setCourse(updated)
    } catch (err) {
      setError(err.message || 'Не удалось опубликовать курс.')
    }
  }

  const archiveCourse = async () => {
    try {
      const updated = await apiRequest(`/courses/${courseId}/archive`, { method: 'PATCH', auth: true })
      setCourse(updated)
    } catch (err) {
      setError(err.message || 'Не удалось архивировать курс.')
    }
  }

  const deleteCourse = async () => {
    try {
      await apiRequest(`/courses/${courseId}`, { method: 'DELETE', auth: true })
      window.location.href = '/'
    } catch (err) {
      if (err?.status && err.status < 500) {
        setError(err.message || 'Не удалось удалить курс.')
      } else {
        console.warn('Delete course warning:', err)
        window.location.href = '/'
      }
    }
  }

  const updateCourse = async (event) => {
    event.preventDefault()
    try {
      const payload = {
        title: editCourseForm.title,
        description: editCourseForm.description || null,
        category_id: editCourseForm.category_id || null,
        level: editCourseForm.level || null,
        price: editCourseForm.price === '' ? null : Number(editCourseForm.price),
        thumbnail_url: editCourseForm.thumbnail_url || null,
      }
      const updated = await apiRequest(`/courses/${courseId}`, {
        method: 'PUT',
        auth: true,
        body: payload,
      })
      setCourse(updated)
      setShowEditCourse(false)
    } catch (err) {
      setError(err.message || 'Не удалось обновить курс.')
    }
  }

  const addSection = async (event) => {
    event.preventDefault()
    setSectionError('')
    try {
      const created = await apiRequest(`/courses/${courseId}/sections`, {
        method: 'POST',
        auth: true,
        body: { title: newSectionTitle },
      })
      setSections((prev) => [...prev, { ...created, lessons: [] }])
      setNewSectionTitle('')
    } catch (err) {
      setSectionError(err.message || 'Не удалось добавить секцию.')
    }
  }

  const updateSection = async (sectionId) => {
    setSectionError('')
    try {
      const updated = await apiRequest(`/courses/${courseId}/sections/${sectionId}`, {
        method: 'PUT',
        auth: true,
        body: { title: editingSectionTitle },
      })
      setSections((prev) => prev.map((section) => (
        section.id === sectionId ? { ...section, title: updated.title } : section
      )))
      setEditingSectionId(null)
      setEditingSectionTitle('')
    } catch (err) {
      setSectionError(err.message || 'Не удалось обновить секцию.')
    }
  }

  const deleteSection = async (sectionId) => {
    setSectionError('')
    let snapshot = []
    setSections((prev) => {
      snapshot = prev
      return prev.filter((section) => section.id !== sectionId)
    })
    try {
      await apiRequest(`/courses/${courseId}/sections/${sectionId}`, { method: 'DELETE', auth: true })
    } catch (err) {
      if (err?.status && err.status < 500) {
        setSections(snapshot)
        setSectionError(err.message || 'Не удалось удалить секцию.')
      } else {
        console.warn('Delete section warning:', err)
      }
    }
  }

  const addLesson = async (sectionId) => {
    const form = newLesson[sectionId]
    if (!form?.title) return
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
      setSections((prev) => prev.map((section) => (
        section.id === sectionId ? { ...section, lessons: [...section.lessons, created] } : section
      )))
      setNewLesson((prev) => ({ ...prev, [sectionId]: {} }))
    } catch (err) {
      setLessonError(err.message || 'Не удалось добавить урок.')
    }
  }

  const updateLesson = async (sectionId, lessonId) => {
    setLessonError('')
    try {
      const updated = await apiRequest(
        `/courses/${courseId}/sections/${sectionId}/lessons/${lessonId}`,
        {
          method: 'PUT',
          auth: true,
          body: {
            title: editingLessonForm.title,
            content: editingLessonForm.content || null,
            lesson_type: editingLessonForm.lesson_type || null,
            video_url: editingLessonForm.video_url || null,
            duration: editingLessonForm.duration ? Number(editingLessonForm.duration) : null,
          },
        },
      )
      setSections((prev) => prev.map((section) => (
        section.id === sectionId
          ? {
            ...section,
            lessons: section.lessons.map((lesson) => (lesson.id === lessonId ? updated : lesson)),
          }
          : section
      )))
      setEditingLessonId(null)
      setEditingLessonForm({})
    } catch (err) {
      setLessonError(err.message || 'Не удалось обновить урок.')
    }
  }

  const deleteLesson = async (sectionId, lessonId) => {
    setLessonError('')
    let snapshot = []
    setSections((prev) => {
      snapshot = prev
      return prev.map((section) => (
        section.id === sectionId
          ? { ...section, lessons: section.lessons.filter((lesson) => lesson.id !== lessonId) }
          : section
      ))
    })
    try {
      await apiRequest(`/courses/${courseId}/sections/${sectionId}/lessons/${lessonId}`, {
        method: 'DELETE',
        auth: true,
      })
    } catch (err) {
      if (err?.status && err.status < 500) {
        setSections(snapshot)
        setLessonError(err.message || 'Не удалось удалить урок.')
      } else {
        console.warn('Delete lesson warning:', err)
      }
    }
  }

  if (status === 'loading') {
    return <div className="page"><div className="empty">Загрузка курса...</div></div>
  }

  if (status === 'error') {
    return <div className="page"><div className="empty">{error}</div></div>
  }

  return (
    <div className="page course-page" id="top">
      <aside className="course-sidebar">
        <div className="course-sidebar__title">Навигация</div>
        <nav className="course-sidebar__nav">
          <a href="#top">Описание курса</a>
          {sections.map((section, index) => (
            <div className="course-sidebar__group" key={section.id}>
              <a href={`#section-${section.id}`}>{index + 1}. {section.title}</a>
              <div className="course-sidebar__lessons">
                {section.lessons.map((lesson, lessonIndex) => (
                  <a key={lesson.id} href={`#lesson-${lesson.id}`}>
                    {index + 1}.{lessonIndex + 1} {lesson.title}
                  </a>
                ))}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      <div className="course-content">
        <section className="section section--hero">
          <div className="course-hero">
            <div>
              <Link className="link-back" to="/">← Назад к каталогу</Link>
              <h2>{course.title}</h2>
              <div id="course-description">
                <CourseDescription
                  description={course.description}
                  showFull={showFullDescription}
                  onToggle={() => setShowFullDescription((prev) => !prev)}
                />
              </div>
              <div className="course-hero__meta">
                <span>{levelLabels[course.level] || 'Любой уровень'}</span>
                <span>{formatPrice(course.price)}</span>
                <span className={`badge badge--${course.status.toLowerCase()}`}>{course.status}</span>
              </div>
            </div>
            <div className="course-hero__aside">
              <div className="panel">
                <div className="panel__body">
                  <div className="stat-card stat-card--inline">
                    <div className="stat-card__value">{totalLessons}</div>
                    <div className="stat-card__label">Уроков</div>
                  </div>
                  <div className="stat-card stat-card--inline">
                    <div className="stat-card__value">{progressPercent}%</div>
                    <div className="stat-card__label">Прогресс</div>
                  </div>
                  {isAuthenticated && enrollment ? (
                    <div className="pill">
                      Статус: {enrollmentStatusLabels[enrollment.status] || enrollment.status}
                    </div>
                  ) : course.status === 'DRAFT' ? (
                    <div className="pill">Курс в разработке</div>
                  ) : (
                    <button className="button" type="button" onClick={enroll} disabled={!isAuthenticated}>
                      {isAuthenticated ? 'Записаться' : 'Войдите, чтобы записаться'}
                    </button>
                  )}
                </div>
              </div>
              {canManageCourse && (
                <div className="panel">
                  <div className="panel__body">
                    <div className="panel__title">Управление курсом</div>
                    <div className="button-row">
                      <button className="button button--ghost" type="button" onClick={() => setShowEditCourse(true)}>
                        Редактировать
                      </button>
                      <button className="button button--ghost" type="button" onClick={publishCourse}>
                        Опубликовать
                      </button>
                      <button className="button button--ghost" type="button" onClick={archiveCourse}>
                        Архивировать
                      </button>
                      <button className="button button--danger" type="button" onClick={deleteCourse}>
                        Удалить
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {error && <div className="form-error">{error}</div>}
        {enrollment?.status === 'COMPLETED' && (
          <div className="success-banner">
            Поздравляем! Курс завершен, прогресс 100%.
          </div>
        )}

        <section className="section">
        <div className="section__header">
          <div>
            <h3>Секции и уроки</h3>
            <p>Полная структура курса с прогрессом по урокам.</p>
          </div>
        </div>
        {sectionError && <div className="form-error">{sectionError}</div>}
        {lessonError && <div className="form-error">{lessonError}</div>}

        {canManageCourse && (
          <form className="panel panel--inline" onSubmit={addSection}>
            <div className="input-group input-group--inline">
              <label htmlFor="new-section">Новая секция</label>
              <input
                id="new-section"
                value={newSectionTitle}
                onChange={(event) => setNewSectionTitle(event.target.value)}
                placeholder="Название секции"
                required
              />
            </div>
            <button className="button" type="submit">Добавить</button>
          </form>
        )}

        <div className="section-list">
          {sections.map((section) => (
            <div className="section-card" key={section.id} id={`section-${section.id}`}>
              <div className="section-card__header">
                {editingSectionId === section.id ? (
                  <div className="inline-edit">
                    <input
                      value={editingSectionTitle}
                      onChange={(event) => setEditingSectionTitle(event.target.value)}
                    />
                    <button className="button button--ghost" type="button" onClick={() => updateSection(section.id)}>
                      Сохранить
                    </button>
                    <button className="button button--ghost" type="button" onClick={() => setEditingSectionId(null)}>
                      Отмена
                    </button>
                  </div>
                ) : (
                  <>
                    <h4>{section.title}</h4>
                    {canManageCourse && (
                      <div className="button-row">
                        <button
                          className="button button--ghost"
                          type="button"
                          onClick={() => {
                            setEditingSectionId(section.id)
                            setEditingSectionTitle(section.title)
                          }}
                        >
                          Редактировать
                        </button>
                        <button className="button button--danger" type="button" onClick={() => deleteSection(section.id)}>
                          Удалить
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>

              <div className="lesson-list">
                {section.lessons.length === 0 && <div className="empty">Пока нет уроков.</div>}
                {section.lessons.map((lesson) => {
                  const progress = lessonProgress[lesson.id]
                  return (
                    <div className="lesson-card" key={lesson.id} id={`lesson-${lesson.id}`}>
                      <div className="lesson-card__body">
                        <div>
                          <div className="lesson-card__title">{lesson.title}</div>
                          <div className="lesson-card__meta">
                            {lessonTypeLabels[lesson.lesson_type] || lesson.lesson_type}
                            {lesson.duration ? ` · ${lesson.duration} мин` : ''}
                          </div>
                          {lesson.content && (
                            <p className="lesson-card__content">
                              {markdownToText(lesson.content)}
                            </p>
                          )}
                          {lesson.video_url && (
                            <a className="link" href={lesson.video_url} target="_blank" rel="noreferrer">
                              Открыть видео
                            </a>
                          )}
                        </div>
                        <div className="lesson-card__aside">
                          <div
                            className={`pill ${progress?.status === 'COMPLETED' ? 'pill--success' : ''}`}
                          >
                            {progress?.status
                              ? lessonProgressLabels[progress.status] || progress.status
                              : 'Без прогресса'}
                          </div>
                          {enrollment && (
                            <Link
                              className="button button--ghost"
                              to={`/courses/${courseId}/sections/${section.id}/lessons/${lesson.id}`}
                            >
                              Открыть урок
                            </Link>
                          )}
                        </div>
                      </div>

                      {canManageCourse && (
                        <div className="lesson-card__editor">
                          {editingLessonId === lesson.id ? (
                            <div className="lesson-edit-grid">
                              <input
                                value={editingLessonForm.title || ''}
                                onChange={(event) => setEditingLessonForm((prev) => ({ ...prev, title: event.target.value }))}
                              />
                              <select
                                value={editingLessonForm.lesson_type || ''}
                                onChange={(event) => setEditingLessonForm((prev) => ({ ...prev, lesson_type: event.target.value }))}
                              >
                                <option value="">Тип урока</option>
                                <option value="TEXT">Текст</option>
                                <option value="VIDEO">Видео</option>
                                <option value="QUIZ">Тест</option>
                              </select>
                              <input
                                value={editingLessonForm.duration || ''}
                                onChange={(event) => setEditingLessonForm((prev) => ({ ...prev, duration: event.target.value }))}
                                placeholder="Длительность, мин"
                                type="number"
                                min="0"
                              />
                              <input
                                value={editingLessonForm.video_url || ''}
                                onChange={(event) => setEditingLessonForm((prev) => ({ ...prev, video_url: event.target.value }))}
                                placeholder="Ссылка на видео"
                              />
                              <textarea
                                value={editingLessonForm.content || ''}
                                onChange={(event) => setEditingLessonForm((prev) => ({ ...prev, content: event.target.value }))}
                                rows="2"
                                placeholder="Описание"
                              />
                              <div className="button-row">
                                <button
                                  className="button button--ghost"
                                  type="button"
                                  onClick={() => updateLesson(section.id, lesson.id)}
                                >
                                  Сохранить
                                </button>
                                <button
                                  className="button button--ghost"
                                  type="button"
                                  onClick={() => setEditingLessonId(null)}
                                >
                                  Отмена
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="button-row">
                              <button
                                className="button button--ghost"
                                type="button"
                                onClick={() => {
                                  setEditingLessonId(lesson.id)
                                  setEditingLessonForm({
                                    title: lesson.title,
                                    content: lesson.content || '',
                                    lesson_type: lesson.lesson_type || '',
                                    video_url: lesson.video_url || '',
                                    duration: lesson.duration || '',
                                  })
                                }}
                              >
                                Редактировать
                              </button>
                              <button
                                className="button button--danger"
                                type="button"
                                onClick={() => deleteLesson(section.id, lesson.id)}
                              >
                                Удалить
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {canManageCourse && (
                <div className="lesson-create">
                  <h5>Новый урок</h5>
                  <div className="lesson-create__form">
                    <input
                      placeholder="Название"
                      value={newLesson[section.id]?.title || ''}
                      onChange={(event) =>
                        setNewLesson((prev) => ({
                          ...prev,
                          [section.id]: { ...prev[section.id], title: event.target.value },
                        }))
                      }
                    />
                    <select
                      value={newLesson[section.id]?.lesson_type || ''}
                      onChange={(event) =>
                        setNewLesson((prev) => ({
                          ...prev,
                          [section.id]: { ...prev[section.id], lesson_type: event.target.value },
                        }))
                      }
                    >
                      <option value="">Тип урока</option>
                      <option value="TEXT">Текст</option>
                      <option value="VIDEO">Видео</option>
                      <option value="QUIZ">Тест</option>
                    </select>
                    <input
                      placeholder="Длительность, мин"
                      type="number"
                      min="0"
                      value={newLesson[section.id]?.duration || ''}
                      onChange={(event) =>
                        setNewLesson((prev) => ({
                          ...prev,
                          [section.id]: { ...prev[section.id], duration: event.target.value },
                        }))
                      }
                    />
                    <input
                      placeholder="Ссылка на видео"
                      value={newLesson[section.id]?.video_url || ''}
                      onChange={(event) =>
                        setNewLesson((prev) => ({
                          ...prev,
                          [section.id]: { ...prev[section.id], video_url: event.target.value },
                        }))
                      }
                    />
                    <textarea
                      placeholder="Описание"
                      rows="2"
                      value={newLesson[section.id]?.content || ''}
                      onChange={(event) =>
                        setNewLesson((prev) => ({
                          ...prev,
                          [section.id]: { ...prev[section.id], content: event.target.value },
                        }))
                      }
                    />
                    <button className="button" type="button" onClick={() => addLesson(section.id)}>
                      Добавить урок
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        </section>
      </div>

      {showEditCourse && (
        <div className="modal-backdrop" role="presentation" onClick={() => setShowEditCourse(false)}>
          <div className="modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
            <div className="modal__header">
              <h4>Редактировать курс</h4>
              <button className="button button--ghost" type="button" onClick={() => setShowEditCourse(false)}>
                Закрыть
              </button>
            </div>
            <form onSubmit={updateCourse}>
              <div className="modal__body">
                <div className="input-group">
                  <label htmlFor="edit-title">Название</label>
                  <input
                    id="edit-title"
                    value={editCourseForm.title}
                    onChange={(event) => setEditCourseForm((prev) => ({ ...prev, title: event.target.value }))}
                    required
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="edit-description">Описание</label>
                  <textarea
                    id="edit-description"
                    rows="4"
                    value={editCourseForm.description}
                    onChange={(event) => setEditCourseForm((prev) => ({ ...prev, description: event.target.value }))}
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="edit-category">Категория</label>
                  <select
                    id="edit-category"
                    value={editCourseForm.category_id}
                    onChange={(event) => setEditCourseForm((prev) => ({ ...prev, category_id: event.target.value }))}
                  >
                    <option value="">Без категории</option>
                    {categories.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="input-group">
                  <label htmlFor="edit-level">Уровень</label>
                  <select
                    id="edit-level"
                    value={editCourseForm.level}
                    onChange={(event) => setEditCourseForm((prev) => ({ ...prev, level: event.target.value }))}
                  >
                    <option value="">Любой</option>
                    <option value="BEGINNER">Начальный</option>
                    <option value="INTERMEDIATE">Средний</option>
                    <option value="ADVANCED">Продвинутый</option>
                  </select>
                </div>
                <div className="input-group">
                  <label htmlFor="edit-price">Стоимость</label>
                  <input
                    id="edit-price"
                    type="number"
                    min="0"
                    value={editCourseForm.price}
                    onChange={(event) => setEditCourseForm((prev) => ({ ...prev, price: event.target.value }))}
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="edit-thumbnail">Ссылка на обложку</label>
                  <input
                    id="edit-thumbnail"
                    value={editCourseForm.thumbnail_url}
                    onChange={(event) => setEditCourseForm((prev) => ({ ...prev, thumbnail_url: event.target.value }))}
                  />
                </div>
              </div>
              <div className="modal__footer">
                <button className="button" type="submit">Сохранить</button>
                <button className="button button--ghost" type="button" onClick={() => setShowEditCourse(false)}>
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

function CourseDescription({ description, showFull, onToggle }) {
  const text = description || 'Описание пока не добавлено.'
  const plain = markdownToText(text)
  const isLong = plain.length > 420

  if (!isLong) {
    return (
      <div
        className="course-description markdown"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(text) }}
      />
    )
  }

  if (showFull) {
    return (
      <>
        <div
          className="course-description markdown"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(text) }}
        />
        <button className="button button--ghost" type="button" onClick={onToggle}>
          Свернуть
        </button>
      </>
    )
  }

  return (
    <>
      <p className="course-description-preview">{plain}</p>
      <button className="button button--ghost" type="button" onClick={onToggle}>
        Дальше
      </button>
    </>
  )
}
