import { useState } from 'react'

export default function CategoryRow({ category, onUpdate, onDelete }) {
  const [name, setName] = useState(category.name)
  return (
    <div className="list-row" key={category.id}>
      <div>
        <div className="list-row__title">{category.name}</div>
        <div className="list-row__meta">slug: {category.slug}</div>
      </div>
      <div className="list-row__actions">
        <input
          key={`${category.id}-${category.name}`}
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
