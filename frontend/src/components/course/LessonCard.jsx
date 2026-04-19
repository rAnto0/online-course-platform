import { Link } from 'react-router-dom'
import { lessonProgressLabels, lessonTypeLabels } from '../../utils/format.js'
import { markdownToText } from '../../utils/markdown.js'

export default function LessonCard({
  lesson,
  sectionId,
  courseId,
  enrollment,
  progress,
  canManageCourse,
  isEditing,
  editingForm,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onDelete,
  onFormChange,
}) {
  if (isEditing) {
    return (
      <div className="lesson-card">
        <div className="lesson-card__editor">
          <div className="lesson-edit-grid">
            <input
              value={editingForm.title || ''}
              onChange={onFormChange('title')}
            />
            <select
              value={editingForm.lesson_type || ''}
              onChange={onFormChange('lesson_type')}
            >
              <option value="">Тип урока</option>
              <option value="TEXT">Текст</option>
              <option value="VIDEO">Видео</option>
              <option value="QUIZ">Тест</option>
            </select>
            <input
              value={editingForm.duration || ''}
              onChange={onFormChange('duration')}
              placeholder="Длительность, мин"
              type="number"
              min="0"
            />
            <input
              value={editingForm.video_url || ''}
              onChange={onFormChange('video_url')}
              placeholder="Ссылка на видео"
            />
            <textarea
              value={editingForm.content || ''}
              onChange={onFormChange('content')}
              rows="2"
              placeholder="Описание"
            />
            <div className="button-row">
              <button className="button button--ghost" type="button" onClick={onSaveEdit}>
                Сохранить
              </button>
              <button className="button button--ghost" type="button" onClick={onCancelEdit}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="lesson-card" id={`lesson-${lesson.id}`}>
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
              to={`/courses/${courseId}/sections/${sectionId}/lessons/${lesson.id}`}
            >
              Открыть урок
            </Link>
          )}
        </div>
      </div>

      {canManageCourse && (
        <div className="lesson-card__editor">
          <div className="button-row">
            <button
              className="button button--ghost"
              type="button"
              onClick={onStartEdit}
            >
              Редактировать
            </button>
            <button
              className="button button--danger"
              type="button"
              onClick={onDelete}
            >
              Удалить
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
