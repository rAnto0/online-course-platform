import { useMemo } from 'react'

export default function Pagination({ page, totalPages, hasNextPage, onPageChange }) {
  const visiblePages = useMemo(() => {
    if (totalPages <= 5) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }
    let start = Math.max(1, page - 2)
    let end = start + 4
    if (end > totalPages) {
      end = totalPages
      start = Math.max(1, end - 4)
    }
    return Array.from({ length: end - start + 1 }, (_, i) => start + i)
  }, [totalPages, page])

  if (totalPages <= 1) return null
  if (page === 1 && !hasNextPage) return null

  return (
    <div className="pagination">
      <button
        className="button button--ghost"
        type="button"
        onClick={() => onPageChange(Math.max(1, page - 1))}
        disabled={page === 1}
      >
        Назад
      </button>
      <div className="pagination__pages">
        {visiblePages.map((p) => (
          <button
            key={p}
            className={`pagination__page ${p === page ? 'is-active' : ''}`}
            type="button"
            onClick={() => onPageChange(p)}
          >
            {p}
          </button>
        ))}
      </div>
      <div className="pagination__info">
        Страница {page} из {totalPages}
      </div>
      <button
        className="button button--ghost"
        type="button"
        onClick={() => onPageChange(page + 1)}
        disabled={!hasNextPage}
      >
        Вперед
      </button>
    </div>
  )
}
