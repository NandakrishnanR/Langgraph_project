import { useState } from 'react'
import './CodeDisplay.css'

export default function CodeDisplay({ code }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="code-display-wrapper">
      <div className="code-header">
        <h3>Generated Python Code</h3>
        <button className="copy-btn" onClick={handleCopy}>
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="code-block">{code}</pre>
      <div className="code-info">
        <small>Ready to use. Optimized for your data.</small>
      </div>
    </div>
  )
}
