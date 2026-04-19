import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { levelLabels, formatPrice } from '../../utils/format.js'
import Pagination from '../Pagination.jsx'

export default function CourseList({ courses, user, onCreateClick }) {
  const [adminCoursePage, setAdminCoursePage] = useState(1)
  const adminCoursesPerPage = 10
  const isAdmin = user?.role === 'admin'

  const myCourses = useMemo(() => {
    if (isAdmin) return courses
    return courses.filter((course) => course.author_id === user?.id)
  }, [courses, user, isAdmin])

  const adminCourses = useMemo(() => (isAdmin ? myCourses : []), [isAdmin, myCourses])
  const adminTotalPages = Math.max(1, Math.ceil(adminCourses.length / adminCoursesPerPage))
  const clampedAdminPage = useMemo(() => Math.min(adminCoursePage, adminTotalPages), [adminCoursePage, adminTotalPages])
  const adminPagedCourses = useMemo(() => {
    const start = (clampedAdminPage - 1) * adminCoursesPerPage
    return adminCourses.slice(start, start + adminCoursesPerPage)
  }, [adminCourses, clampedAdminPage])
  const adminHasNextPage = clampedAdminPage < adminTotalPages

  const displayCourses = isAdmin ? adminPagedCourses : myCourses

  const title = isAdmin ? 'Курсы' : 'Мои курсы'
  const subtitle = isAdmin ? 'Курсы, которые вы администрируете' : 'Все курсы, которые вы создавали.'
  const panelTitle = isAdmin ? 'Все курсы на платформе' : 'Мои курсы'

  return (
    <section className="section">
      <div className="section__header">
        <div>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>
        <button className="button" type="button" onClick={onCreateClick}>
          Создать курс
        </button>
      </div>
      <div className="panel panel--wide">
        <div className="panel__header">
          <h4>{panelTitle}</h4>
        </div>
        <div className="panel__body">
          {displayCourses.length === 0 && <div className="empty">Пока нет курсов.</div>}
          {displayCourses.map((course) => (
            <div className="list-row" key={course.id}>
              <div>
                <div className="list-row__title">
                  {course.title}
                  <span className={`badge badge--${course.status.toLowerCase()}`}>{course.status}</span>
                </div>
                <div className="list-row__meta">
                  {levelLabels[course.level] || 'Любой уровень'} · {formatPrice(course.price)}
                </div>
              </div>
              <Link className="button button--ghost" to={`/courses/${course.id}`}>
                Открыть
              </Link>
            </div>
          ))}
        </div>
        {isAdmin && (clampedAdminPage > 1 || adminHasNextPage) && (
          <div className="panel__footer">
            <Pagination
              page={clampedAdminPage}
              totalPages={adminTotalPages}
              hasNextPage={adminHasNextPage}
              onPageChange={setAdminCoursePage}
            />
          </div>
        )}
      </div>
    </section>
  )
}
