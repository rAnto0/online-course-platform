import { useCallback, useMemo, useState } from 'react'
import { apiRequest, normalizeCollection } from '../../utils/apiClient.js'
import Pagination from '../Pagination.jsx'
import CategoryRow from './CategoryRow.jsx'

export default function CategoryManager({ categories: propCategories, setCategories: propSetCategories }) {
  const categories = useMemo(() => propCategories ?? [], [propCategories])
  const setCategories = useMemo(() => propSetCategories ?? (() => {}), [propSetCategories])
  const [form, setForm] = useState({ name: '' })
  const [status, setStatus] = useState('idle')
  const [createError, setCreateError] = useState('')
  const [listError, setListError] = useState('')
  const [page, setPage] = useState(1)
  const perPage = 10

  const totalPages = Math.max(1, Math.ceil(categories.length / perPage))
  const clampedPage = useMemo(() => Math.min(page, totalPages), [page, totalPages])
  const pagedCategories = useMemo(() => {
    const start = (clampedPage - 1) * perPage
    return categories.slice(start, start + perPage)
  }, [categories, clampedPage])
  const hasNextPage = clampedPage < totalPages

  const refreshTotals = useCallback(async () => {
    try {
      const categoriesData = await apiRequest('/categories', { method: 'GET', auth: false })
      const refreshed = normalizeCollection(categoriesData)
      setCategories(refreshed)
      setListError('')
    } catch (err) {
      setListError(err.message || 'Не удалось обновить категории.')
    }
  }, [setCategories])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus('loading')
    setCreateError('')
    try {
      const created = await apiRequest('/categories', {
        method: 'POST',
        auth: true,
        body: { name: form.name },
      })
      setCategories((prev) => [created, ...prev])
      setForm({ name: '' })
      setStatus('idle')
      setPage(1)
    } catch (err) {
      setCreateError(err.message || 'Не удалось создать категорию.')
      setStatus('idle')
    }
  }

  const updateCategory = async (categoryId, name) => {
    try {
      const updated = await apiRequest(`/categories/${categoryId}`, {
        method: 'PUT',
        auth: true,
        body: { name },
      })
      setCategories((prev) => prev.map((cat) => (cat.id === categoryId ? updated : cat)))
    } catch (err) {
      setListError(err.message || 'Не удалось обновить категорию.')
    }
  }

  const deleteCategory = async (categoryId) => {
    setListError('')
    const deletedCategory = categories.find((cat) => cat.id === categoryId)
    if (!deletedCategory) return
    const deletedIndex = categories.findIndex((cat) => cat.id === categoryId)
    setCategories((prev) => prev.filter((cat) => cat.id !== categoryId))
    try {
      await apiRequest(`/categories/${categoryId}`, { method: 'DELETE', auth: true })
      try {
        await refreshTotals()
      } catch {
        // refresh error already set by refreshTotals
      }
    } catch (err) {
      setCategories((prev) => {
        const exists = prev.find((cat) => cat.id === categoryId)
        if (exists) return prev
        const next = [...prev]
        const index = deletedIndex < 0 ? next.length : Math.min(deletedIndex, next.length)
        next.splice(index, 0, deletedCategory)
        return next
      })
      setListError(err.message || 'Не удалось удалить категорию.')
    }
  }

  return (
    <section className="section">
      <div className="section__header">
        <div>
          <h3>Категории (админ)</h3>
          <p>Создавайте и редактируйте категории каталога.</p>
        </div>
      </div>
      <div className="panel panel--wide">
        <div className="panel__header panel__header--split">
          <div>
            <h4>Категории</h4>
            <p>Добавляйте новые и редактируйте существующие.</p>
          </div>
          <form className="category-toolbar" onSubmit={handleSubmit}>
            <div className="input-group input-group--inline">
              <label htmlFor="category-name">Название</label>
              <input
                id="category-name"
                value={form.name}
                onChange={(event) => setForm({ name: event.target.value })}
                required
              />
            </div>
            <button className="button" type="submit" disabled={status === 'loading'}>
              {status === 'loading' ? 'Сохраняем...' : 'Добавить'}
            </button>
          </form>
        </div>
        {createError && <div className="form-error">{createError}</div>}
        <div className="panel__body">
          {listError && <div className="form-error">{listError}</div>}
          {pagedCategories.length === 0 && <div className="empty">Категорий пока нет.</div>}
          {pagedCategories.map((category) => (
            <CategoryRow
              key={category.id}
              category={category}
              onUpdate={updateCategory}
              onDelete={deleteCategory}
            />
          ))}
        </div>
        {(clampedPage > 1 || hasNextPage) && (
          <div className="panel__footer">
            <Pagination
              page={clampedPage}
              totalPages={totalPages}
              hasNextPage={hasNextPage}
              onPageChange={setPage}
            />
          </div>
        )}
      </div>
    </section>
  )
}
