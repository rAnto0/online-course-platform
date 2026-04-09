import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest, normalizeCollection } from '../utils/apiClient.js'
import { enrollmentStatusLabels, formatPrice, levelLabels } from '../utils/format.js'
import { useAuth } from '../state/AuthContext.jsx'

const emptyCourseForm = {
  title: '',
  description: '',
  category_id: '',
  level: '',
  price: '',
  thumbnail_url: '',
}

export default function Dashboard() {
  const { user, refreshSession } = useAuth()
  const [courses, setCourses] = useState([])
  const [categories, setCategories] = useState([])
  const [enrollments, setEnrollments] = useState([])
  const [courseForm, setCourseForm] = useState(emptyCourseForm)
  const [courseStatus, setCourseStatus] = useState('idle')
  const [error, setError] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [adminCoursePage, setAdminCoursePage] = useState(1)
  const adminCoursesPerPage = 10
  const [enrollmentPage, setEnrollmentPage] = useState(1)
  const enrollmentsPerPage = 10

  const isAdmin = user?.role === 'admin'
  const safeCategories = Array.isArray(categories) ? categories : []
  const safeCourses = Array.isArray(courses) ? courses : []

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const [coursesData, categoriesData] = await Promise.all([
          apiRequest('/courses?skip=0&limit=1000', { method: 'GET', auth: false }),
          apiRequest('/categories', { method: 'GET', auth: false }),
        ])

        if (mounted) {
          setCourses(normalizeCollection(coursesData))
          setCategories(normalizeCollection(categoriesData))
        }

        if (mounted && user) {
          const enrollmentsData = await apiRequest('/progress/enrollments/by-user', {
            method: 'GET',
            auth: true,
          })
          const safeEnrollments = normalizeCollection(enrollmentsData)
          const enriched = await Promise.all(
            safeEnrollments.map(async (enrollment) => {
              try {
                const course = await apiRequest(`/courses/${enrollment.course_id}`, {
                  method: 'GET',
                  auth: false,
                })
                return { ...enrollment, course, courseError: null }
              } catch (error) {
                const message = error?.status === 404
                  ? 'Курс удален или скрыт'
                  : 'Курс временно недоступен'
                return { ...enrollment, course: null, courseError: message }
              }
            }),
          )
          setEnrollments(enriched)
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || 'Не удалось загрузить данные кабинета.')
        }
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [user])

  const myCourses = useMemo(() => {
    if (!user) return []
    if (user.role === 'admin') return courses
    return safeCourses.filter((course) => course.author_id === user.id)
  }, [safeCourses, user])

  const enrollmentTotalPages = Math.max(1, Math.ceil(enrollments.length / enrollmentsPerPage))
  const pagedEnrollments = useMemo(() => {
    const start = (enrollmentPage - 1) * enrollmentsPerPage
    return enrollments.slice(start, start + enrollmentsPerPage)
  }, [enrollments, enrollmentPage])
  const enrollmentHasNextPage = enrollmentPage < enrollmentTotalPages
  const enrollmentVisiblePages = useMemo(() => {
    if (enrollmentTotalPages <= 5) {
      return Array.from({ length: enrollmentTotalPages }, (_, i) => i + 1)
    }
    let start = Math.max(1, enrollmentPage - 2)
    let end = start + 4
    if (end > enrollmentTotalPages) {
      end = enrollmentTotalPages
      start = Math.max(1, end - 4)
    }
    return Array.from({ length: end - start + 1 }, (_, i) => start + i)
  }, [enrollmentTotalPages, enrollmentPage])

  useEffect(() => {
    if (enrollmentPage > enrollmentTotalPages) {
      setEnrollmentPage(enrollmentTotalPages)
    }
  }, [enrollmentPage, enrollmentTotalPages])

  const adminCourses = useMemo(() => (
    user?.role === 'admin' ? myCourses : []
  ), [myCourses, user])

  const adminTotalPages = Math.max(1, Math.ceil(adminCourses.length / adminCoursesPerPage))
  const adminPagedCourses = useMemo(() => {
    const start = (adminCoursePage - 1) * adminCoursesPerPage
    return adminCourses.slice(start, start + adminCoursesPerPage)
  }, [adminCourses, adminCoursePage])
  const adminHasNextPage = adminCoursePage < adminTotalPages
  const adminVisiblePages = useMemo(() => {
    if (adminTotalPages <= 5) {
      return Array.from({ length: adminTotalPages }, (_, i) => i + 1)
    }
    let start = Math.max(1, adminCoursePage - 2)
    let end = start + 4
    if (end > adminTotalPages) {
      end = adminTotalPages
      start = Math.max(1, end - 4)
    }
    return Array.from({ length: end - start + 1 }, (_, i) => start + i)
  }, [adminTotalPages, adminCoursePage])

  useEffect(() => {
    if (user?.role === 'admin' && adminCoursePage > adminTotalPages) {
      setAdminCoursePage(adminTotalPages)
    }
  }, [adminCoursePage, adminTotalPages, user])

  const handleCourseChange = (event) => {
    const { name, value } = event.target
    setCourseForm((prev) => ({ ...prev, [name]: value }))
  }

  const createCourse = async (event) => {
    event.preventDefault()
    setCourseStatus('loading')
    setError('')
    try {
      const payload = {
        title: courseForm.title,
        description: courseForm.description || null,
        category_id: courseForm.category_id || null,
        level: courseForm.level || null,
        price: courseForm.price ? Number(courseForm.price) : null,
        thumbnail_url: courseForm.thumbnail_url || null,
      }
      const created = await apiRequest('/courses', {
        method: 'POST',
        auth: true,
        body: payload,
      })
      setCourses((prev) => [created, ...prev])
      try {
        await refreshSession()
      } catch (err) {
        console.warn('Role refresh warning:', err)
      }
      setCourseForm(emptyCourseForm)
      setShowCreateModal(false)
      setCourseStatus('idle')
    } catch (err) {
      setError(err.message || 'Не удалось создать курс.')
      setCourseStatus('idle')
    }
  }

  return (
    <div className="page">
      <section className="section">
        <div className="section__header">
          <div>
            <h2>Кабинет</h2>
            <p>Управляйте курсами, категориями и своим обучением.</p>
          </div>
        </div>
        {error && <div className="form-error">{error}</div>}
      </section>

      {user && (
        <section className="section">
          <div className="section__header">
            <div>
              <h3>{user?.role === 'admin' ? 'Курсы' : 'Курсы автора курсы'}</h3>
              <p>{user?.role === 'admin' ? 'Курсы, которые вы администрируете' : 'Все курсы, которые вы создавали.'}</p>
            </div>
            <button className="button" type="button" onClick={() => setShowCreateModal(true)}>
              Создать курс
            </button>
          </div>
          <div className="panel panel--wide">
            <div className="panel__header">
              <h4>{user?.role === 'admin' ? 'Все курсы на платформе' : 'Мои курсы'}</h4>
            </div>
            <div className="panel__body">
              {myCourses.length === 0 && <div className="empty">Пока нет курсов.</div>}
              {(user?.role === 'admin' ? adminPagedCourses : myCourses).map((course) => (
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
            {user?.role === 'admin' && (adminCoursePage > 1 || adminHasNextPage) && (
              <div className="panel__footer">
                <div className="pagination">
                  <button
                    className="button button--ghost"
                    type="button"
                    onClick={() => setAdminCoursePage((p) => Math.max(1, p - 1))}
                    disabled={adminCoursePage === 1}
                  >
                    Назад
                  </button>
                  <div className="pagination__pages">
                    {adminVisiblePages.map((p) => (
                      <button
                        key={p}
                        className={`pagination__page ${p === adminCoursePage ? 'is-active' : ''}`}
                        type="button"
                        onClick={() => setAdminCoursePage(p)}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                  <div className="pagination__info">
                    Страница {adminCoursePage} из {adminTotalPages}
                  </div>
                  <button
                    className="button button--ghost"
                    type="button"
                    onClick={() => setAdminCoursePage((p) => p + 1)}
                    disabled={!adminHasNextPage}
                  >
                    Вперед
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {showCreateModal && (
        <div className="modal-backdrop" role="presentation" onClick={() => setShowCreateModal(false)}>
          <div className="modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
            <div className="modal__header">
              <h4>Новый курс</h4>
              <button className="button button--ghost" type="button" onClick={() => setShowCreateModal(false)}>
                Закрыть
              </button>
            </div>
            <form onSubmit={createCourse}>
              <div className="modal__body">
                <div className="input-group">
                  <label htmlFor="title">Название</label>
                  <input
                    id="title"
                    name="title"
                    value={courseForm.title}
                    onChange={handleCourseChange}
                    required
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="description">Описание</label>
                  <textarea
                    id="description"
                    name="description"
                    value={courseForm.description}
                    onChange={handleCourseChange}
                    rows="3"
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="category_id">Категория</label>
                  <select
                    id="category_id"
                    name="category_id"
                    value={courseForm.category_id}
                    onChange={handleCourseChange}
                  >
                    <option value="">Без категории</option>
                    {safeCategories.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="input-group">
                  <label htmlFor="level">Уровень</label>
                  <select
                    id="level"
                    name="level"
                    value={courseForm.level}
                    onChange={handleCourseChange}
                  >
                    <option value="">Любой</option>
                    <option value="BEGINNER">Начальный</option>
                    <option value="INTERMEDIATE">Средний</option>
                    <option value="ADVANCED">Продвинутый</option>
                  </select>
                </div>
                <div className="input-group">
                  <label htmlFor="price">Стоимость</label>
                  <input
                    id="price"
                    name="price"
                    type="number"
                    min="0"
                    value={courseForm.price}
                    onChange={handleCourseChange}
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="thumbnail_url">Ссылка на обложку</label>
                  <input
                    id="thumbnail_url"
                    name="thumbnail_url"
                    value={courseForm.thumbnail_url}
                    onChange={handleCourseChange}
                  />
                </div>
              </div>
              <div className="modal__footer">
                <button className="button" type="submit" disabled={courseStatus === 'loading'}>
                  {courseStatus === 'loading' ? 'Создаем...' : 'Создать курс'}
                </button>
                <button className="button button--ghost" type="button" onClick={() => setShowCreateModal(false)}>
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {user && (
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
            {(enrollmentPage > 1 || enrollmentHasNextPage) && (
              <div className="panel__footer">
                <div className="pagination">
                  <button
                    className="button button--ghost"
                    type="button"
                    onClick={() => setEnrollmentPage((p) => Math.max(1, p - 1))}
                    disabled={enrollmentPage === 1}
                  >
                    Назад
                  </button>
                  <div className="pagination__pages">
                    {enrollmentVisiblePages.map((p) => (
                      <button
                        key={p}
                        className={`pagination__page ${p === enrollmentPage ? 'is-active' : ''}`}
                        type="button"
                        onClick={() => setEnrollmentPage(p)}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                  <div className="pagination__info">
                    Страница {enrollmentPage} из {enrollmentTotalPages}
                  </div>
                  <button
                    className="button button--ghost"
                    type="button"
                    onClick={() => setEnrollmentPage((p) => p + 1)}
                    disabled={!enrollmentHasNextPage}
                  >
                    Вперед
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {isAdmin && (
        <CategoryManager categories={safeCategories} setCategories={setCategories} />
      )}
    </div>
  )
}

function CategoryManager({ categories, setCategories }) {
  const [form, setForm] = useState({ name: '' })
  const [status, setStatus] = useState('idle')
  const [createError, setCreateError] = useState('')
  const [listError, setListError] = useState('')
  const [page, setPage] = useState(1)
  const perPage = 10
  const totalPages = Math.max(1, Math.ceil(categories.length / perPage))
  const pagedCategories = useMemo(() => {
    const start = (page - 1) * perPage
    return categories.slice(start, start + perPage)
  }, [categories, page])
  const hasNextPage = page < totalPages
  const visiblePages = useMemo(() => {
    if (totalPages <= 5) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }
    let start = Math.max(1, page - 2)
    let end = start + 4
    if (end > totalPages) {
      end = totalPages
      start = Math.max(1, end - 4)
    }
    return Array.from({ length: end - start + 1 }, (_, i) => start + i)
  }, [totalPages, page])

  useEffect(() => {
    let mounted = true
    const loadTotal = async () => {
      try {
        const categoriesData = await apiRequest('/categories?skip=0&limit=10000', { method: 'GET', auth: false })
        if (!mounted) return
        const all = normalizeCollection(categoriesData)
        setCategories(all)
        setListError('')
      } catch (err) {
        if (mounted) {
          setListError(err.message || 'Не удалось загрузить категории.')
        }
      }
    }
    loadTotal()
    return () => {
      mounted = false
    }
  }, [setCategories])

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages)
    }
  }, [page, totalPages])

  const refreshTotals = async () => {
    try {
      const categoriesData = await apiRequest('/categories?skip=0&limit=10000', { method: 'GET', auth: false })
      const all = normalizeCollection(categoriesData)
      setCategories(all)
      setListError('')
      return all.length
    } catch (err) {
      setListError(err.message || 'Не удалось загрузить категории.')
      return null
    }
  }

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
      await refreshTotals()
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
    let snapshot = []
    setCategories((prev) => {
      snapshot = prev
      return prev.filter((cat) => cat.id !== categoryId)
    })
    try {
      await apiRequest(`/categories/${categoryId}`, {
        method: 'DELETE',
        auth: true,
      })
      await refreshTotals()
    } catch (err) {
      if (err?.status && err.status < 500) {
        setCategories(snapshot)
        setListError(err.message || 'Не удалось удалить категорию.')
      } else {
        console.warn('Delete category warning:', err)
      }
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
        {(page > 1 || hasNextPage) && (
          <div className="panel__footer">
            <div className="pagination">
              <button
                className="button button--ghost"
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Назад
              </button>
              <div className="pagination__pages">
                {visiblePages.map((p) => (
                  <button
                    key={p}
                    className={`pagination__page ${p === page ? 'is-active' : ''}`}
                    type="button"
                    onClick={() => setPage(p)}
                  >
                    {p}
                  </button>
                ))}
              </div>
              <div className="pagination__info">
                Страница {page} из {totalPages}
              </div>
              <button
                className="button button--ghost"
                type="button"
                onClick={() => setPage((p) => p + 1)}
                disabled={!hasNextPage}
              >
                Вперед
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

function CategoryRow({ category, onUpdate, onDelete }) {
  const [name, setName] = useState(category.name)
  return (
    <div className="list-row">
      <div>
        <div className="list-row__title">{category.name}</div>
        <div className="list-row__meta">slug: {category.slug}</div>
      </div>
      <div className="list-row__actions">
        <input
          className="input-inline"
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
        <button className="button button--ghost" type="button" onClick={() => onUpdate(category.id, name)}>
          Обновить
        </button>
        <button className="button button--danger" type="button" onClick={() => onDelete(category.id)}>
          Удалить
        </button>
      </div>
    </div>
  )
}
