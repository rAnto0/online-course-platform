import SectionCard from './SectionCard.jsx'

export default function SectionList({
  sections,
  courseId,
  enrollment,
  lessonProgress,
  canManageCourse,
  editingSectionId,
  editingSectionTitle,
  editingLessonId,
  editingLessonForm,
  actions,
}) {
  return (
    <div className="section-list">
      {sections.map((section) => (
        <SectionCard
          key={section.id}
          section={section}
          courseId={courseId}
          enrollment={enrollment}
          lessonProgress={lessonProgress}
          canManageCourse={canManageCourse}
          editingSectionId={editingSectionId}
          editingSectionTitle={editingSectionTitle}
          editingLessonId={editingLessonId}
          editingLessonForm={editingLessonForm}
          onStartEditSection={() => actions.onStartEditSection(section.id, section.title)}
          onSaveEditSection={() => actions.onSaveEditSection(section.id)}
          onCancelEditSection={() => actions.onCancelEditSection()}
          onSectionTitleChange={actions.onSectionTitleChange}
          onDeleteSection={() => actions.onDeleteSection(section.id)}
          onStartEditLesson={actions.onStartEditLesson}
          onSaveEditLesson={actions.onSaveEditLesson}
          onCancelEditLesson={actions.onCancelEditLesson}
          onDeleteLesson={actions.onDeleteLesson}
          onLessonFormChange={actions.onLessonFormChange}
          onAddLesson={actions.onAddLesson}
        />
      ))}
    </div>
  )
}
