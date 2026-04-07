import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext.jsx'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [form, setForm] = useState({ username: '', password: '' })
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
      await login(form)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Не удалось войти.')
      setStatus('idle')
    }
  }

  return (
    <div className="page page--center">
      <form className="panel" onSubmit={handleSubmit}>
        <div className="panel__header">
          <h2>Добро пожаловать</h2>
          <p>Войдите, чтобы управлять курсами и прогрессом.</p>
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
            <label htmlFor="password">Пароль</label>
            <input
              id="password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Введите пароль"
              required
            />
          </div>
          {error && <div className="form-error">{error}</div>}
        </div>
        <div className="panel__footer">
          <button className="button" type="submit" disabled={status === 'loading'}>
            {status === 'loading' ? 'Входим...' : 'Войти'}
          </button>
          <Link className="button button--ghost" to="/register">
            Создать аккаунт
          </Link>
        </div>
      </form>
    </div>
  )
}
