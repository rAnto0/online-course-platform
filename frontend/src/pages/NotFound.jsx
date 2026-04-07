import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="page page--center">
      <div className="panel">
        <div className="panel__header">
          <h2>Страница не найдена</h2>
          <p>Такого маршрута нет. Вернемся в каталог.</p>
        </div>
        <div className="panel__footer">
          <Link className="button" to="/">Перейти в каталог</Link>
        </div>
      </div>
    </div>
  )
}
