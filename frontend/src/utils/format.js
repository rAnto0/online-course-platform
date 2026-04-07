export function formatDate(value) {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

export function formatPrice(value) {
  if (value === null || value === undefined) return 'Бесплатно'
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(value)
}

export const levelLabels = {
  BEGINNER: 'Начальный',
  INTERMEDIATE: 'Средний',
  ADVANCED: 'Продвинутый',
}

export const lessonTypeLabels = {
  TEXT: 'Текстовый урок',
  VIDEO: 'Видео',
  QUIZ: 'Тест',
}

export const enrollmentStatusLabels = {
  ACTIVE: 'Активно',
  COMPLETED: 'Завершено',
  DROPPED: 'Приостановлено',
}

export const lessonProgressLabels = {
  NOT_STARTED: 'Не начат',
  IN_PROGRESS: 'В процессе',
  COMPLETED: 'Завершен',
}
