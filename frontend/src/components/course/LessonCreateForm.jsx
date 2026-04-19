import { useState } from 'react'

export default function LessonCreateForm({ sectionId, onAdd }) {
  const [form, setForm] = useState({
    title: '',
    lesson_type: '',
    duration: '',
    video_url: '',
    content: '',
  })

  const update = (field) => (event) =>
    setForm((prev) => ({ ...prev, [field]: event.target.value }))

  const handleAdd = () => {
    if (!form.title?.trim()) return
    onAdd(sectionId, form)
    setForm({ title: '', lesson_type: '', duration: '', video_url: '', content: '' })
  }

  return (
    <div className="lesson-create">
      <h5>Новый урок</h5>
      <div className="lesson-create__form">
        <input
          placeholder="Название"
          value={form.title}
          onChange={update('title')}
        />
        <select value={form.lesson_type} onChange={update('lesson_type')}>
          <option value="">Тип урока</option>
          <option value="TEXT">Текст</option>
          <option value="VIDEO">Видео</option>
          <option value="QUIZ">Тест</option>
        </select>
        <input
          placeholder="Длительность, мин"
          type="number"
          min="0"
          value={form.duration}
          onChange={update('duration')}
        />
        <input
          placeholder="Ссылка на видео"
          value={form.video_url}
          onChange={update('video_url')}
        />
        <textarea
          placeholder="Описание"
          rows="2"
          value={form.content}
          onChange={update('content')}
        />
        <button className="button" type="button" onClick={handleAdd}>
          Добавить урок
        </button>
      </div>
    </div>
  )
}
