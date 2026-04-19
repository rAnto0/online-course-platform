import { markdownToText, renderMarkdown } from '../../utils/markdown.js'

export default function CourseDescription({ description, showFull, onToggle }) {
  const text = description || 'Описание пока не добавлено.'
  const plain = markdownToText(text)
  const isLong = plain.length > 420

  if (!isLong) {
    return (
      <div
        className="course-description markdown"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(text) }}
      />
    )
  }

  if (showFull) {
    return (
      <>
        <div
          className="course-description markdown"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(text) }}
        />
        <button className="button button--ghost" type="button" onClick={onToggle}>
          Свернуть
        </button>
      </>
    )
  }

  return (
    <>
      <p className="course-description-preview">{plain}</p>
      <button className="button button--ghost" type="button" onClick={onToggle}>
        Дальше
      </button>
    </>
  )
}
