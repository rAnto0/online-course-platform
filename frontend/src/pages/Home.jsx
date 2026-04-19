import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest, normalizeCollection } from '../utils/apiClient.js'
import { formatPrice, levelLabels } from '../utils/format.js'
import { markdownToText } from '../utils/markdown.js'
import Pagination from '../components/Pagination.jsx'

export default function Home() {
  const [courses, setCourses] = useState([])
  const [categories, setCategories] = useState([])
  const [status, setStatus] = useState('loading')
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [page, setPage] = useState(1)

  const coursesWithPreview = useMemo(() => (
    courses.map((course) => ({
      ...course,
      preview: markdownToText(course.description),
    }))
  ), [courses])

  useEffect(() => {
    let mounted = true
    const loadCategories = async () => {
      try {
        const categoriesData = await apiRequest('/categories', { method: 'GET', auth: false })
        if (mounted) {
          setCategories(normalizeCollection(categoriesData))
        }
      } catch {
        if (mounted) {
          setCategories([])
        }
      }
    }
    loadCategories()
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    let mounted = true
    const loadCourses = async () => {
      try {
        const coursesData = await apiRequest('/courses?skip=0&limit=10000', { method: 'GET', auth: false })
        if (mounted) {
          const allCourses = normalizeCollection(coursesData)
          setCourses(allCourses)
          setStatus('ready')
        }
      } catch {
        if (mounted) {
          setStatus('error')
        }
      }
    }
    loadCourses()
    return () => {
      mounted = false
    }
  }, [])

  const filteredCourses = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return coursesWithPreview.filter((course) => {
      if (course.status === 'DRAFT' || course.status === 'ARCHIVED') {
        return false
      }
      const matchesSearch = !needle
        || course.title.toLowerCase().includes(needle)
        || (course.preview || '').toLowerCase().includes(needle)
      const matchesCategory = categoryFilter === 'all' || course.category_id === categoryFilter
      return matchesSearch && matchesCategory
    })
  }, [coursesWithPreview, search, categoryFilter])

  const totalPages = Math.max(1, Math.ceil(filteredCourses.length / 9))
  const clampedPage = useMemo(() => Math.min(page, totalPages), [page, totalPages])
  const totalCourses = useMemo(() => {
    return courses.filter((c) => c.status !== 'DRAFT' && c.status !== 'ARCHIVED').length
  }, [courses])

  const pagedCourses = useMemo(() => {
    const start = (clampedPage - 1) * 9
    return filteredCourses.slice(start, start + 9)
  }, [filteredCourses, clampedPage])
  const hasNextPage = clampedPage < totalPages

  return (
    <div className="page">
      <section className="hero">
        <div className="hero__content">
          <p className="eyebrow">Платформа онлайн-обучения</p>
          <h1>Запускайте курсы, растите сообщество и управляйте знаниями в одном месте.</h1>
          <p className="hero__lead">
            Каталог, витрина, личные кабинеты, прогресс и инструменты для авторов —
            все, чтобы развивать образовательный продукт как бизнес.
          </p>
          <div className="hero__actions">
            <Link className="button" to="/register">Начать обучение</Link>
            <Link className="button button--ghost" to="/login">Войти в кабинет</Link>
          </div>
        </div>
          <div className="hero__stats">
            <div className="stat-card">
              <div className="stat-card__value">{totalCourses}</div>
              <div className="stat-card__label">Курсов на платформе</div>
            </div>
            <div className="stat-card">
              <div className="stat-card__value">{categories.length}</div>
              <div className="stat-card__label">Направлений обучения</div>
            </div>
          </div>
      </section>

      <section className="section">
        <div className="section__header">
          <div>
            <h2>Каталог курсов</h2>
            <p>Выберите направление и стартуйте обучение.</p>
          </div>
          <div className="filters">
            <div className="input-group">
              <label htmlFor="course-search">Поиск</label>
              <input
                id="course-search"
                type="search"
                placeholder="Название или описание"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
            <div className="input-group">
              <label htmlFor="course-category">Категория</label>
              <select
                id="course-category"
                value={categoryFilter}
                onChange={(event) => setCategoryFilter(event.target.value)}
              >
                <option value="all">Все категории</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {status === 'loading' && <div className="empty">Загрузка курсов...</div>}
        {status === 'error' && (
          <div className="empty">Не удалось загрузить каталог. Проверьте API Gateway.</div>
        )}

        {status === 'ready' && filteredCourses.length === 0 && (
          <div className="empty">Пока нет курсов. Создайте новый в кабинете преподавателя.</div>
        )}

        <div className="grid">
          {pagedCourses.map((course) => (
            <article className="card" key={course.id}>
              <div className="card__header">
                <div>
                  <h3>{course.title}</h3>
                  <p>{course.preview || 'Описание пока не добавлено.'}</p>
                </div>
                <span className={`badge badge--${course.status.toLowerCase()}`}>
                  {course.status}
                </span>
              </div>
              <div className="card__meta">
                <span>{levelLabels[course.level] || 'Любой уровень'}</span>
                <span>{formatPrice(course.price)}</span>
              </div>
              <div className="card__actions">
                <Link className="button button--ghost" to={`/courses/${course.id}`}>
                  Подробнее
                </Link>
              </div>
            </article>
          ))}
        </div>

        {(clampedPage > 1 || hasNextPage) && (
          <Pagination
            page={clampedPage}
            totalPages={totalPages}
            hasNextPage={hasNextPage}
            onPageChange={setPage}
          />
        )}
      </section>
    </div>
  )
}
