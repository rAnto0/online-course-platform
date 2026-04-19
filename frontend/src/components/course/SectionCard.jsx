import LessonCard from './LessonCard.jsx'
import LessonCreateForm from './LessonCreateForm.jsx'

export default function SectionCard({
  section,
  courseId,
  enrollment,
  lessonProgress,
  canManageCourse,
  editingSectionId,
  editingSectionTitle,
  editingLessonId,
  editingLessonForm,
  onStartEditSection,
  onSaveEditSection,
  onCancelEditSection,
  onSectionTitleChange,
  onDeleteSection,
  onStartEditLesson,
  onSaveEditLesson,
  onCancelEditLesson,
  onDeleteLesson,
  onLessonFormChange,
  onAddLesson,
}) {
  const isEditingSection = editingSectionId === section.id

  return (
    <div className="section-card" id={`section-${section.id}`}>
      <div className="section-card__header">
        {isEditingSection ? (
          <div className="inline-edit">
            <input
              value={editingSectionTitle}
              onChange={(event) => onSectionTitleChange(event.target.value)}
            />
            <button className="button button--ghost" type="button" onClick={onSaveEditSection}>
              Сохранить
            </button>
            <button className="button button--ghost" type="button" onClick={onCancelEditSection}>
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
                  onClick={onStartEditSection}
                >
                  Редактировать
                </button>
                <button
                  className="button button--danger"
                  type="button"
                  onClick={onDeleteSection}
                >
                  Удалить
                </button>
              </div>
            )}
          </>
        )}
      </div>

      <div className="lesson-list">
        {section.lessons.length === 0 && <div className="empty">Пока нет уроков.</div>}
        {section.lessons.map((lesson) => (
          <LessonCard
            key={lesson.id}
            lesson={lesson}
            sectionId={section.id}
            courseId={courseId}
            enrollment={enrollment}
            progress={lessonProgress[lesson.id]}
            canManageCourse={canManageCourse}
            isEditing={editingLessonId === lesson.id}
            editingForm={editingLessonForm}
            onStartEdit={() => onStartEditLesson(lesson)}
            onCancelEdit={onCancelEditLesson}
            onSaveEdit={() => onSaveEditLesson(section.id, lesson.id)}
            onDelete={() => onDeleteLesson(section.id, lesson.id)}
            onFormChange={(field) => (event) => onLessonFormChange(field, event.target.value)}
          />
        ))}
      </div>

      {canManageCourse && (
        <LessonCreateForm sectionId={section.id} onAdd={onAddLesson} />
      )}
    </div>
  )
}
