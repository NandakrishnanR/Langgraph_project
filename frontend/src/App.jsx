import { useState } from 'react'
import axios from 'axios'
import './App.css'

const baseAgents = [
  { id: 1, title: 'DataCleaner', emoji: '🧹', color: '#3b82f6' },
  { id: 2, title: 'AlgorithmSelector', emoji: '🎯', color: '#1e40af' },
  { id: 3, title: 'CodeGenerator', emoji: '⚡', color: '#1e3a8a' }
]

function App() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [agents, setAgents] = useState(baseAgents.map(a => ({ ...a, status: 'pending' })))
  const [messages, setMessages] = useState([])
  const [generatedCode, setGeneratedCode] = useState('')
  const [copied, setCopied] = useState(false)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile)
      setError('')
      setMessages([])
      setGeneratedCode('')
      setAgents(baseAgents.map(a => ({ ...a, status: 'pending' })))
    } else {
      setError('Please select a valid CSV file')
    }
  }

  const runWorkflow = async () => {
    if (!file) {
      setError('Please upload a CSV file first')
      return
    }
    setLoading(true)
    setError('')
    setMessages([])
    setGeneratedCode('')

    // Simulate agent progression
    const updateAgent = (idx) => {
      setAgents(prev => prev.map((a, i) => ({
        ...a,
        status: i < idx ? 'completed' : i === idx ? 'in-progress' : 'pending'
      })))
    }

    updateAgent(0)
    setTimeout(() => updateAgent(1), 2000)
    setTimeout(() => updateAgent(2), 4000)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await axios.post('/api/run', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      const conversation = res.data?.messages || []
      const code = res.data?.code || ''

      setAgents(baseAgents.map(a => ({ ...a, status: 'completed' })))
      setMessages(conversation)
      setGeneratedCode(code)
    } catch (err) {
      const msg = err.response?.data?.error || 'Analysis failed. Check backend server and Ollama.'
      setError(msg)
      setAgents(baseAgents.map(a => ({ ...a, status: 'failed' })))
    } finally {
      setLoading(false)
    }
  }

  const copyCode = () => {
    navigator.clipboard.writeText(generatedCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo-container">
            <img src="/MR_Logo.webp" alt="MR Logo" />
          </div>
          <div className="title-section">
            <h1 className="title">ML Algorithm Advisor</h1>
            <p className="subtitle">Powered by LangGraph + Ollama llama3.1</p>
            <p className="description">Upload CSV -> Auto-analyze -> Get best ML algorithm + Python code</p>
          </div>
        </div>
      </header>

      <div className="container">
        <div className="top-section">
          <div className="mini-card upload-card">
            <h3>📊 Upload Dataset</h3>
            <p className="mini-text">Select a CSV to begin</p>
            <div className="mini-actions">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                disabled={loading}
                id="file-input"
                style={{ display: 'none' }}
              />
              <label htmlFor="file-input" className="mini-btn primary">
                {file ? '🔁 Replace CSV' : '📁 Upload CSV'}
              </label>
              <button
                type="button"
                className="mini-btn secondary"
                onClick={runWorkflow}
                disabled={loading || !file}
              >
                {loading ? '⏳ Analyzing...' : ' Analyze'}
              </button>
            </div>
            <p className="mini-meta">{file ? file.name : 'Awaiting file selection'}</p>
            {error && <div className="mini-error"> {error}</div>}
          </div>

          {agents.map((agent) => (
            <div
              key={agent.id}
              className="mini-card agent-card"
              style={{ borderColor: agent.color }}
            >
              <div className="agent-number">Agent {agent.id}</div>
              <div className="agent-emoji">{agent.emoji}</div>
              <div className="agent-title">{agent.title}</div>
              <div className={`agent-badge ${agent.status}`}>{agent.status}</div>
            </div>
          ))}
        </div>

        <div className="grid">
          <div className="panel results-panel">
            <div className="panel-header">
              <h3>💬 Agent Analysis</h3>
            </div>
            <div className="messages">
              {messages.length === 0 && <p className="muted">Upload a CSV to start analysis</p>}
              {messages.map((msg, idx) => {
                const role = (msg.role || '').toLowerCase()
                if (role === 'user' || role === 'human') {
                  return null
                }
                const roleLabel = msg.role ? msg.role.toUpperCase() : 'AGENT'
                return (
                  <div key={idx} className="message">
                    <div className="message-role">📍 {roleLabel}</div>
                    <div className="message-content">{msg.content}</div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="panel results-panel">
            <div className="panel-header">
              <h3>📈 Quick Summary</h3>
            </div>
            <div className="messages">
              {messages.length === 0 && <p className="muted">Results will appear here</p>}
              {messages.length > 0 && (
                <div className="message">
                  <div className="message-content">
                    <strong>Dataset Processed </strong><br/>
                    {messages.length} agent responses generated
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {generatedCode && (
          <div className="panel code-panel">
            <div className="panel-header">
              <h3>🐍 Generated Python Code</h3>
              <button className="btn-copy" onClick={copyCode}>
                {copied ? '✓ Copied!' : '📋 Copy Code'}
              </button>
            </div>
            {generatedCode.trim() ? (
              <pre className="code-block">{generatedCode}</pre>
            ) : (
              <p className="muted">Code generation in progress or no code extracted...</p>
            )}
          </div>
        )}
      </div>

      <footer className="footer">
        <p>© MIT License(only for demo purpose) • LangGraph • Local Ollama Integration</p>
      </footer>
    </div>
  )
}

export default App
