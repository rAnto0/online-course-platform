import { useState } from 'react'

export default function CourseEditModal({ course, categories, onSave, onClose }) {
  const safeCategories = Array.isArray(categories) ? categories : []
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  const [form, setForm] = useState({
    title: course?.title || '',
    description: course?.description || '',
    category_id: course?.category_id || '',
    level: course?.level || '',
    price: course?.price ?? '',
    thumbnail_url: course?.thumbnail_url || '',
  })

  if (!course) return null

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setSaveError('')
    try {
      const success = await onSave({
        title: form.title,
        description: form.description || null,
        category_id: form.category_id || null,
        level: form.level || null,
        price: form.price === '' ? null : Number(form.price),
        thumbnail_url: form.thumbnail_url || null,
      })
      if (success) {
        onClose()
      }
    } catch (err) {
      setSaveError(err.message || 'Не удалось обновить курс.')
    } finally {
      setSaving(false)
    }
  }

  const update = (field) => (event) =>
    setForm((prev) => ({ ...prev, [field]: event.target.value }))

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
        <div className="modal__header">
          <h4>Редактировать курс</h4>
          <button className="button button--ghost" type="button" onClick={onClose}>
            Закрыть
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal__body">
            <div className="input-group">
              <label htmlFor="edit-title">Название</label>
              <input id="edit-title" value={form.title} onChange={update('title')} required />
            </div>
            <div className="input-group">
              <label htmlFor="edit-description">Описание</label>
              <textarea id="edit-description" rows="4" value={form.description} onChange={update('description')} />
            </div>
            <div className="input-group">
              <label htmlFor="edit-category">Категория</label>
              <select id="edit-category" value={form.category_id} onChange={update('category_id')}>
                <option value="">Без категории</option>
                {safeCategories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            <div className="input-group">
              <label htmlFor="edit-level">Уровень</label>
              <select id="edit-level" value={form.level} onChange={update('level')}>
                <option value="">Любой</option>
                <option value="BEGINNER">Начальный</option>
                <option value="INTERMEDIATE">Средний</option>
                <option value="ADVANCED">Продвинутый</option>
              </select>
            </div>
            <div className="input-group">
              <label htmlFor="edit-price">Стоимость</label>
              <input id="edit-price" type="number" min="0" value={form.price} onChange={update('price')} />
            </div>
            <div className="input-group">
              <label htmlFor="edit-thumbnail">Ссылка на обложку</label>
              <input id="edit-thumbnail" value={form.thumbnail_url} onChange={update('thumbnail_url')} />
            </div>
          </div>
          <div className="modal__footer">
            {saveError && <div className="form-error">{saveError}</div>}
            <button className="button" type="submit" disabled={saving}>
              {saving ? 'Сохраняем...' : 'Сохранить'}
            </button>
            <button className="button button--ghost" type="button" onClick={onClose}>
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
