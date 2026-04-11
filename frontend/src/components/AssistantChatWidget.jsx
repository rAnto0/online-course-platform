import { useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest } from '../utils/apiClient.js'

const START_MESSAGE = {
  role: 'assistant',
  content: 'Привет! Я помогу подобрать курс по цели, уровню и бюджету.',
  recommended_courses: [],
}

export default function AssistantChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([START_MESSAGE])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const scrollRef = useRef(null)

  const history = useMemo(
    () => messages.map((item) => ({ role: item.role, content: item.content })),
    [messages],
  )

  const sendMessage = async (event) => {
    event.preventDefault()
    const message = input.trim()
    if (!message || isLoading) return

    const nextMessages = [...messages, { role: 'user', content: message, recommended_courses: [] }]
    setMessages(nextMessages)
    setInput('')
    setError('')
    setIsLoading(true)

    try {
      const data = await apiRequest('/assistant/chat', {
        method: 'POST',
        auth: false,
        body: {
          message,
          history,
        },
      })

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data?.answer || 'Не удалось получить ответ.',
          recommended_courses: Array.isArray(data?.recommended_courses) ? data.recommended_courses : [],
        },
      ])
    } catch (requestError) {
      setError(requestError.message || 'Ошибка при обращении к ассистенту.')
    } finally {
      setIsLoading(false)
      setTimeout(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
      }, 0)
    }
  }

  return (
    <div className="assistant">
      {isOpen && (
        <section className="assistant__panel" aria-label="Чат-помощник">
          <header className="assistant__header">
            <h3>ИИ-помощник</h3>
            <button
              className="assistant__icon-button"
              type="button"
              onClick={() => setIsOpen(false)}
              aria-label="Закрыть чат"
            >
              ×
            </button>
          </header>

          <div className="assistant__messages" ref={scrollRef}>
            {messages.map((message, index) => (
              <article
                key={`${message.role}-${index}`}
                className={`assistant__message assistant__message--${message.role}`}
              >
                <p>{message.content}</p>
                {message.role === 'assistant' && message.recommended_courses?.length > 0 && (
                  <div className="assistant__recommendations">
                    {message.recommended_courses.map((course) => (
                      <div className="assistant__course" key={course.course_id}>
                        <div className="assistant__course-title">{course.title}</div>
                        <div className="assistant__course-reason">{course.reason}</div>
                        <Link className="button button--ghost" to={`/courses/${course.course_id}`}>
                          Открыть курс
                        </Link>
                      </div>
                    ))}
                  </div>
                )}
              </article>
            ))}
            {isLoading && <div className="assistant__typing">Ассистент печатает...</div>}
          </div>

          <form className="assistant__form" onSubmit={sendMessage}>
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Например: хочу курс по Python для новичка"
              disabled={isLoading}
            />
            <button className="button" type="submit" disabled={isLoading || !input.trim()}>
              Отправить
            </button>
          </form>
          {error && <div className="assistant__error">{error}</div>}
        </section>
      )}

      <button
        className="assistant__toggle"
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
      >
        {isOpen ? 'Скрыть чат' : 'Открыть чат'}
      </button>
    </div>
  )
}
