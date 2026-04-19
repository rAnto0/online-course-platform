export default function CourseManagementPanel({ onEdit, onPublish, onArchive, onDelete }) {
  return (
    <div className="panel">
      <div className="panel__body">
        <div className="panel__title">Управление курсом</div>
        <div className="button-row">
          <button className="button button--ghost" type="button" onClick={onEdit}>
            Редактировать
          </button>
          <button className="button button--ghost" type="button" onClick={onPublish}>
            Опубликовать
          </button>
          <button className="button button--ghost" type="button" onClick={onArchive}>
            Архивировать
          </button>
          <button className="button button--danger" type="button" onClick={onDelete}>
            Удалить
          </button>
        </div>
      </div>
    </div>
  )
}
