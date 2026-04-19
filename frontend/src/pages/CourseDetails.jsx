import { useCallback, useMemo, useRef, useState } from 'react'
import { useAuth } from '../state/AuthContext.jsx'
import { useParams } from 'react-router-dom'
import useCourseData from '../hooks/useCourseData.js'
import useCourseActions from '../hooks/useCourseActions.js'
import CourseSidebar from '../components/course/CourseSidebar.jsx'
import CourseHero from '../components/course/CourseHero.jsx'
import SectionList from '../components/course/SectionList.jsx'
import CourseEditModal from '../components/course/CourseEditModal.jsx'

export default function CourseDetails() {
  const { courseId } = useParams()
  const { user, isAuthenticated } = useAuth()

  // Data loading
  const {
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
    setError,
    totalLessons,
    progressPercent,
  } = useCourseData(courseId)

  // Actions
  const {
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
  } = useCourseActions(courseId)

  // UI state
  const [showFullDescription, setShowFullDescription] = useState(false)
  const [showEditCourse, setShowEditCourse] = useState(false)
  const [newSectionTitle, setNewSectionTitle] = useState('')
  const [editingSectionId, setEditingSectionId] = useState(null)
  const [editingSectionTitle, setEditingSectionTitle] = useState('')
  const [editingLessonId, setEditingLessonId] = useState(null)
  const [editingLessonForm, setEditingLessonForm] = useState({})
  const editingLessonFormRef = useRef({})
  const [isAddingSection, setIsAddingSection] = useState(false)
  const [isEnrolling, setIsEnrolling] = useState(false)
  const editingSectionTitleRef = useRef('')

  const isOwner = Boolean(user && course && user.id === course.author_id)
  const canManageCourse = Boolean(user && course && (user.role === 'admin' || isOwner))

  // Sync course updates from actions
  const handlePublish = async () => {
    const updated = await publishCourse()
    if (updated) setCourse(updated)
  }

  const handleArchive = async () => {
    if (!confirm('Вы уверены, что хотите архивировать этот курс?')) return
    const updated = await archiveCourse()
    if (updated) setCourse(updated)
  }

  const handleEditCourse = async (payload) => {
    const updated = await updateCourse(payload)
    if (updated) {
      setCourse(updated)
      return true
    }
    setError('Не удалось обновить курс.')
    return false
  }

  const handleEnroll = async () => {
    if (isEnrolling) return
    setIsEnrolling(true)
    try {
      const result = await enroll()
      if (result) {
        setEnrollment(result)
      }
    } finally {
      setIsEnrolling(false)
    }
  }

  const handleStartEditSection = useCallback((sectionId, title) => {
    setEditingSectionId(sectionId)
    setEditingSectionTitle(title)
    editingSectionTitleRef.current = title
  }, [])

  const handleSaveEditSection = useCallback(async (sectionId) => {
    const title = editingSectionTitleRef.current
    if (!title.trim()) return
    const updated = await updateSection(sectionId, title)
    if (updated) {
      setSections((prev) =>
        prev.map((s) => (s.id === sectionId ? { ...s, title: updated.title } : s))
      )
    }
    setEditingSectionId(null)
    setEditingSectionTitle('')
    editingSectionTitleRef.current = ''
  }, [updateSection, setSections])

  const handleCancelEditSection = useCallback(() => {
    setEditingSectionId(null)
    setEditingSectionTitle('')
    editingSectionTitleRef.current = ''
  }, [])

  const handleStartEditLesson = useCallback((lesson) => {
    const form = {
      title: lesson.title,
      content: lesson.content || '',
      lesson_type: lesson.lesson_type || '',
      video_url: lesson.video_url || '',
      duration: lesson.duration || '',
    }
    setEditingLessonId(lesson.id)
    setEditingLessonForm(form)
    editingLessonFormRef.current = form
  }, [])

  const handleSaveEditLesson = useCallback(async (sectionId, lessonId) => {
    const form = editingLessonFormRef.current
    const updated = await updateLesson(sectionId, lessonId, form)
    if (updated) {
      setSections((prev) =>
        prev.map((s) =>
          s.id === sectionId
            ? { ...s, lessons: s.lessons.map((l) => (l.id === lessonId ? updated : l)) }
            : s
        )
      )
    }
    setEditingLessonId(null)
    setEditingLessonForm({})
    editingLessonFormRef.current = {}
  }, [updateLesson, setSections])

  const handleCancelEditLesson = useCallback(() => {
    setEditingLessonId(null)
    setEditingLessonForm({})
    editingLessonFormRef.current = {}
  }, [])

  const handleLessonFormChange = useCallback((field, value) => {
    const updated = { ...editingLessonFormRef.current, [field]: value }
    setEditingLessonForm(updated)
    editingLessonFormRef.current = updated
  }, [])

  const handleAddLesson = useCallback(async (sectionId, form) => {
    const created = await addLesson(sectionId, form)
    if (created) {
      setSections((prev) =>
        prev.map((s) =>
          s.id === sectionId ? { ...s, lessons: [...s.lessons, created] } : s
        )
      )
    }
  }, [addLesson, setSections])

  const handleDeleteSection = useCallback(async (sectionId) => {
    const success = await deleteSection(sectionId)
    if (success) {
      setSections((prev) => prev.filter((s) => s.id !== sectionId))
    }
  }, [deleteSection, setSections])

  const handleDeleteLesson = useCallback(async (sectionId, lessonId) => {
    const success = await deleteLesson(sectionId, lessonId)
    if (success) {
      setSections((prev) =>
        prev.map((s) =>
          s.id === sectionId
            ? { ...s, lessons: s.lessons.filter((l) => l.id !== lessonId) }
            : s
        )
      )
    }
  }, [deleteLesson, setSections])

  const actions = useMemo(() => ({
    onStartEditSection: handleStartEditSection,
    onSaveEditSection: handleSaveEditSection,
    onCancelEditSection: handleCancelEditSection,
    onSectionTitleChange: (value) => {
      setEditingSectionTitle(value)
      editingSectionTitleRef.current = value
    },
    onDeleteSection: handleDeleteSection,
    onStartEditLesson: handleStartEditLesson,
    onSaveEditLesson: handleSaveEditLesson,
    onCancelEditLesson: handleCancelEditLesson,
    onDeleteLesson: handleDeleteLesson,
    onLessonFormChange: handleLessonFormChange,
    onAddLesson: handleAddLesson,
  }), [
    handleStartEditSection,
    handleSaveEditSection,
    handleCancelEditSection,
    handleDeleteSection,
    handleSaveEditLesson,
    handleCancelEditLesson,
    handleStartEditLesson,
    handleDeleteLesson,
    handleLessonFormChange,
    handleAddLesson,
  ])

  if (status === 'loading') {
    return <div className="page"><div className="empty">Загрузка курса...</div></div>
  }

  if (status === 'error') {
    return <div className="page"><div className="empty">{error}</div></div>
  }

  return (
    <div className="page course-page" id="top">
      <CourseSidebar sections={sections} courseId={courseId} />

      <div className="course-content">
        <CourseHero
          key={course.id}
          course={course}
          totalLessons={totalLessons}
          progressPercent={progressPercent}
          enrollment={enrollment}
          isAuthenticated={isAuthenticated}
          canManageCourse={canManageCourse}
          showFullDescription={showFullDescription}
          onToggleDescription={() => setShowFullDescription((prev) => !prev)}
          onEnroll={handleEnroll}
          isEnrolling={isEnrolling}
          onPublish={handlePublish}
          onArchive={handleArchive}
          onDelete={async () => {
            if (!confirm('Вы уверены, что хотите удалить этот курс? Это действие нельзя отменить.')) return
            const success = await deleteCourse()
            if (!success) setError('Не удалось удалить курс.')
          }}
          onEdit={() => setShowEditCourse(true)}
        />

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
            <form
              className="panel panel--inline"
              onSubmit={async (event) => {
                event.preventDefault()
                if (isAddingSection) return
                setIsAddingSection(true)
                try {
                  const created = await addSection(newSectionTitle)
                  if (created) {
                    setSections((prev) => [...prev, { ...created, lessons: [] }])
                    setNewSectionTitle('')
                  }
                } catch (err) {
                  console.warn('Failed to add section:', err)
                } finally {
                  setIsAddingSection(false)
                }
              }}
            >
              <div className="input-group input-group--inline">
                <label htmlFor="new-section">Новая секция</label>
                <input
                  id="new-section"
                  value={newSectionTitle}
                  onChange={(event) => setNewSectionTitle(event.target.value)}
                  placeholder="Название секции"
                  required
                  disabled={isAddingSection}
                />
              </div>
              <button className="button" type="submit" disabled={isAddingSection}>
                {isAddingSection ? 'Добавление...' : 'Добавить'}
              </button>
            </form>
          )}

          <SectionList
            sections={sections}
            courseId={courseId}
            enrollment={enrollment}
            lessonProgress={lessonProgress}
            canManageCourse={canManageCourse}
            editingSectionId={editingSectionId}
            editingSectionTitle={editingSectionTitle}
            editingLessonId={editingLessonId}
            editingLessonForm={editingLessonForm}
            actions={actions}
          />
        </section>
      </div>

      {showEditCourse && (
        <CourseEditModal
          key={course.id}
          course={course}
          categories={categories}
          onSave={handleEditCourse}
          onClose={() => setShowEditCourse(false)}
        />
      )}
    </div>
  )
}
