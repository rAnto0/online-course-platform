export default function Footer() {
  return (
    <footer className="footer">
      <div>
        <div className="footer__title">Online Course Platform</div>
        <p>Микросервисная платформа для обучения, курсов и прогресса студентов.</p>
      </div>
      <div className="footer__meta">
        <span>API Gateway: `http://localhost:8080`</span>
        <span>Frontend: Vite + React</span>
      </div>
    </footer>
  )
}
