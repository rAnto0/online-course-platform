import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext.jsx'

export default function Register() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [form, setForm] = useState({ username: '', email: '', password: '' })
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
      await register(form)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Не удалось зарегистрироваться.')
      setStatus('idle')
    }
  }

  return (
    <div className="page page--center">
      <form className="panel" onSubmit={handleSubmit}>
        <div className="panel__header">
          <h2>Создайте аккаунт</h2>
          <p>Доступ к курсам, прогрессу и панели преподавателя.</p>
        </div>
        <div className="panel__body">
          <div className="input-group">
            <label htmlFor="username">Никнейм</label>
            <input
              id="username"
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="Введите никнейм"
              required
            />
          </div>
          <div className="input-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              placeholder="you@example.com"
              required
            />
          </div>
          <div className="input-group">
            <label htmlFor="password">Пароль</label>
            <input
              id="password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Придумайте пароль"
              required
            />
          </div>
          {error && <div className="form-error">{error}</div>}
        </div>
        <div className="panel__footer">
          <button className="button" type="submit" disabled={status === 'loading'}>
            {status === 'loading' ? 'Создаем...' : 'Зарегистрироваться'}
          </button>
          <Link className="button button--ghost" to="/login">
            Уже есть аккаунт
          </Link>
        </div>
      </form>
    </div>
  )
}
