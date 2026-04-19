import { useMemo, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'

export default function CourseSidebar({ sections, courseId }) {
  const allSectionIds = useMemo(
    () => new Set(sections.map((s) => s.id)),
    [sections],
  )

  const [expandedSections, setExpandedSections] = useState(() => allSectionIds)

  const toggleSection = useCallback((sectionId) => {
    setExpandedSections((prev) => {
      const next = new Set(prev)
      if (next.has(sectionId)) next.delete(sectionId)
      else next.add(sectionId)
      return next
    })
  }, [])

  const totalLessons = useMemo(
    () => sections.reduce((acc, s) => acc + s.lessons.length, 0),
    [sections],
  )

  const shouldCollapse = totalLessons > 20

  return (
    <aside className="course-sidebar">
      <div className="course-sidebar__title">Навигация</div>
      <nav className="course-sidebar__nav">
        <Link to={`/courses/${courseId}#top`}>Описание курса</Link>
        {sections.map((section, index) => {
          const isExpanded = !shouldCollapse || expandedSections.has(section.id)
          return (
            <div className="course-sidebar__group" key={section.id}>
              <Link
                to={`/courses/${courseId}#section-${section.id}`}
                className="course-sidebar__group-title"
                onClick={(e) => {
                  if (shouldCollapse) toggleSection(section.id)
                  const targetId = `section-${section.id}`
                  const targetEl = document.getElementById(targetId)
                  if (targetEl) {
                    e.preventDefault()
                    window.history.replaceState(null, '', `#${targetId}`)
                    targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
                  }
                }}
              >
                {index + 1}. {section.title}
                {shouldCollapse && (
                  <span className="course-sidebar__toggle">
                    {expandedSections.has(section.id) ? '▼' : '▶'}
                  </span>
                )}
              </Link>
              {isExpanded && (
                <div className="course-sidebar__lessons">
                  {section.lessons.map((lesson, lessonIndex) => (
                    <Link key={lesson.id} to={`/courses/${courseId}#lesson-${lesson.id}`}>
                      {index + 1}.{lessonIndex + 1} {lesson.title}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </nav>
    </aside>
  )
}
