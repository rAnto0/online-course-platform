import { NavLink, Link } from 'react-router-dom'
import { useAuth } from '../state/AuthContext.jsx'

export default function TopBar() {
  const { user, isAuthenticated, logout } = useAuth()

  return (
    <header className="topbar">
      <div className="topbar__brand">
        <Link to="/" className="logo">
          <span className="logo__mark">OCP</span>
          <span className="logo__text">Online Course Platform</span>
        </Link>
      </div>
      <nav className="topbar__nav">
        <NavLink to="/" end>
          Каталог
        </NavLink>
        {isAuthenticated && (
          <NavLink to="/dashboard">
            Кабинет
          </NavLink>
        )}
        {isAuthenticated && (
          <NavLink to="/profile">
            Профиль
          </NavLink>
        )}
      </nav>
      <div className="topbar__actions">
        {!isAuthenticated ? (
          <>
            <Link className="button button--ghost" to="/login">
              Войти
            </Link>
            <Link className="button" to="/register">
              Регистрация
            </Link>
          </>
        ) : (
          <>
            <div className="user-chip">
              <div className="user-chip__name">{user?.username}</div>
              <div className="user-chip__role">{user?.role}</div>
            </div>
            <button className="button button--ghost" type="button" onClick={logout}>
              Выйти
            </button>
          </>
        )}
      </div>
    </header>
  )
}
