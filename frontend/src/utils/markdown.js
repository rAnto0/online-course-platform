import DOMPurify from 'dompurify'
import { marked } from 'marked'

marked.setOptions({
  breaks: true,
  gfm: true,
})

export function renderMarkdown(value) {
  const raw = value || ''
  const html = marked.parse(raw)
  return DOMPurify.sanitize(html)
}

export function markdownToText(value) {
  const raw = value || ''
  const html = marked.parse(raw)
  if (typeof window !== 'undefined' && window.DOMParser) {
    const doc = new window.DOMParser().parseFromString(html, 'text/html')
    return (doc.body.textContent || '').replace(/\s+/g, ' ').trim()
  }
  return html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
}
