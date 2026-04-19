import { useState } from 'react'
import { apiRequest } from '../../utils/apiClient.js'

export default function CreateCourseModal({ categories, onClose, onCreated, refreshSession }) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    category_id: '',
    level: '',
    price: '',
    thumbnail_url: '',
  })
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus('loading')
    setError('')
    try {
      const payload = {
        title: form.title,
        description: form.description || null,
        category_id: form.category_id || null,
        level: form.level || null,
        price: form.price ? Number(form.price) : null,
        thumbnail_url: form.thumbnail_url || null,
      }
      const created = await apiRequest('/courses', {
        method: 'POST',
        auth: true,
        body: payload,
      })
      onCreated(created)
      try {
        await refreshSession()
      } catch (err) {
        console.warn('Role refresh warning:', err)
      }
      onClose()
    } catch (err) {
      setError(err.message || 'Не удалось создать курс.')
      setStatus('idle')
    }
  }

  const safeCategories = Array.isArray(categories) ? categories : []

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
        <div className="modal__header">
          <h4>Новый курс</h4>
          <button className="button button--ghost" type="button" onClick={onClose}>
            Закрыть
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal__body">
            {error && <div className="form-error">{error}</div>}
            <div className="input-group">
              <label htmlFor="title">Название</label>
              <input id="title" name="title" value={form.title} onChange={handleChange} required />
            </div>
            <div className="input-group">
              <label htmlFor="description">Описание</label>
              <textarea id="description" name="description" value={form.description} onChange={handleChange} rows="3" />
            </div>
            <div className="input-group">
              <label htmlFor="category_id">Категория</label>
              <select id="category_id" name="category_id" value={form.category_id} onChange={handleChange}>
                <option value="">Без категории</option>
                {safeCategories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            <div className="input-group">
              <label htmlFor="level">Уровень</label>
              <select id="level" name="level" value={form.level} onChange={handleChange}>
                <option value="">Любой</option>
                <option value="BEGINNER">Начальный</option>
                <option value="INTERMEDIATE">Средний</option>
                <option value="ADVANCED">Продвинутый</option>
              </select>
            </div>
            <div className="input-group">
              <label htmlFor="price">Стоимость</label>
              <input id="price" name="price" type="number" min="0" value={form.price} onChange={handleChange} />
            </div>
            <div className="input-group">
              <label htmlFor="thumbnail_url">Ссылка на обложку</label>
              <input id="thumbnail_url" name="thumbnail_url" value={form.thumbnail_url} onChange={handleChange} />
            </div>
          </div>
          <div className="modal__footer">
            <button className="button" type="submit" disabled={status === 'loading'}>
              {status === 'loading' ? 'Создаем...' : 'Создать курс'}
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
