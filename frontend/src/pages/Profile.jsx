import { useAuth } from '../state/AuthContext.jsx'
import { formatDate } from '../utils/format.js'

export default function Profile() {
  const { user } = useAuth()

  return (
    <div className="page">
      <section className="section">
        <div className="section__header">
          <div>
            <h2>Профиль</h2>
            <p>Данные пользователя и роль в системе.</p>
          </div>
        </div>
        <div className="panel panel--wide">
          <div className="panel__body grid grid--two">
            <div>
              <div className="label">Никнейм</div>
              <div className="value">{user?.username}</div>
            </div>
            <div>
              <div className="label">Email</div>
              <div className="value">{user?.email}</div>
            </div>
            <div>
              <div className="label">ID пользователя</div>
              <div className="value value--mono">{user?.id}</div>
            </div>
            <div>
              <div className="label">Роль</div>
              <div className="value">{user?.role}</div>
            </div>
            <div>
              <div className="label">Дата регистрации</div>
              <div className="value">{formatDate(user?.created_at)}</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
