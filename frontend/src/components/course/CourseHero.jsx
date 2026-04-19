import { Link } from 'react-router-dom'
import { enrollmentStatusLabels, formatPrice, levelLabels } from '../../utils/format.js'
import CourseDescription from './CourseDescription.jsx'
import CourseManagementPanel from './CourseManagementPanel.jsx'

export default function CourseHero({
  course,
  totalLessons,
  progressPercent,
  enrollment,
  isAuthenticated,
  canManageCourse,
  showFullDescription,
  onToggleDescription,
  onEnroll,
  isEnrolling,
  onPublish,
  onArchive,
  onDelete,
  onEdit,
}) {
  return (
    <section className="section section--hero">
      <div className="course-hero">
        <div>
          <Link className="link-back" to="/">← Назад к каталогу</Link>
          <h2>{course.title}</h2>
          <div id="course-description">
            <CourseDescription
              description={course.description}
              showFull={showFullDescription}
              onToggle={onToggleDescription}
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
                <button className="button" type="button" onClick={onEnroll} disabled={!isAuthenticated || isEnrolling}>
                  {isAuthenticated ? 'Записаться' : 'Войдите, чтобы записаться'}
                </button>
              )}
            </div>
          </div>
          {canManageCourse && (
            <CourseManagementPanel
              onEdit={onEdit}
              onPublish={onPublish}
              onArchive={onArchive}
              onDelete={onDelete}
            />
          )}
        </div>
      </div>
    </section>
  )
}
