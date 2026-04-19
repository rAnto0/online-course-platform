import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { enrollmentStatusLabels } from '../../utils/format.js'
import Pagination from '../Pagination.jsx'

export default function EnrollmentList({ enrollments }) {
  const [enrollmentPage, setEnrollmentPage] = useState(1)
  const enrollmentsPerPage = 10

  const enrollmentTotalPages = Math.max(1, Math.ceil(enrollments.length / enrollmentsPerPage))
  const clampedEnrollmentPage = useMemo(() => Math.min(enrollmentPage, enrollmentTotalPages), [enrollmentPage, enrollmentTotalPages])
  const pagedEnrollments = useMemo(() => {
    const start = (clampedEnrollmentPage - 1) * enrollmentsPerPage
    return enrollments.slice(start, start + enrollmentsPerPage)
  }, [enrollments, clampedEnrollmentPage])
  const enrollmentHasNextPage = clampedEnrollmentPage < enrollmentTotalPages

  return (
    <section className="section">
      <div className="section__header">
        <div>
          <h3>Мои обучения</h3>
          <p>Список курсов, на которые вы записаны.</p>
        </div>
      </div>
      <div className="panel panel--wide">
        <div className="panel__body">
          {enrollments.length === 0 && <div className="empty">Пока нет записей.</div>}
          {pagedEnrollments.map((enrollment) => (
            <div
              className={`list-row ${enrollment.status === 'COMPLETED' ? 'list-row--completed' : ''}`}
              key={enrollment.id}
            >
              <div>
                <div className="list-row__title">
                  {enrollment.course?.title || 'Курс недоступен'}
                </div>
                <div className="list-row__meta">
                  {enrollment.courseError
                    ? enrollment.courseError
                    : `Статус: ${enrollmentStatusLabels[enrollment.status] || enrollment.status}`}
                </div>
              </div>
              {enrollment.course ? (
                <Link className="button button--ghost" to={`/courses/${enrollment.course_id}`}>
                  Перейти
                </Link>
              ) : (
                <button className="button button--ghost" type="button" disabled>
                  Недоступен
                </button>
              )}
            </div>
          ))}
        </div>
        {(clampedEnrollmentPage > 1 || enrollmentHasNextPage) && (
          <div className="panel__footer">
            <Pagination
              page={clampedEnrollmentPage}
              totalPages={enrollmentTotalPages}
              hasNextPage={enrollmentHasNextPage}
              onPageChange={setEnrollmentPage}
            />
          </div>
        )}
      </div>
    </section>
  )
}
