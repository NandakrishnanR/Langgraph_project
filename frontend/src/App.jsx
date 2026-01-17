import { useState } from 'react'
import axios from 'axios'
import './App.css'

const baseAgents = [
  { id: 1, title: 'DataCleaner', emoji: '🧹', color: '#6366f1' },
  { id: 2, title: 'AlgorithmSelector', emoji: '🎯', color: '#a855f7' },
  { id: 3, title: 'CodeGenerator', emoji: '⚡', color: '#10b981' }
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
          <h1 className="title">🤖 ML Algorithm Advisor</h1>
          <p className="subtitle">Powered by LangGraph + Ollama llama3.1</p>
          <p className="description">Upload CSV → Auto-analyze → Get best ML algorithm + Python code</p>
        </div>
      </header>

      <div className="container">
        <div className="panel upload-panel">
          <div className="panel-header">
            <h3>📊 Upload Dataset</h3>
            <button className="btn-primary" onClick={runWorkflow} disabled={loading || !file}>
              {loading ? '⏳ Analyzing...' : '🚀 Analyze & Generate'}
            </button>
          </div>
          <div className="upload-area">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              disabled={loading}
              id="file-input"
              style={{ display: 'none' }}
            />
            <label htmlFor="file-input" className="file-label">
              {file ? `✓ ${file.name}` : '📁 Choose CSV file'}
            </label>
          </div>
          {error && <div className="error-card">❌ {error}</div>}
        </div>

        <div className="panel agent-panel">
          <div className="panel-header">
            <h3>🔄 Agent Pipeline</h3>
          </div>
          <div className="agents-grid">
            {agents.map((agent) => (
              <div key={agent.id} className={`agent-box agent-${agent.status}`} style={{ borderColor: agent.color }}>
                <div className="agent-number">Agent {agent.id}</div>
                <div className="agent-emoji">{agent.emoji}</div>
                <div className="agent-title">{agent.title}</div>
                <div className={`agent-badge ${agent.status}`}>{agent.status}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid">
          <div className="panel results-panel">
            <div className="panel-header">
              <h3>💬 Agent Analysis</h3>
            </div>
            <div className="messages">
              {messages.length === 0 && <p className="muted">Upload a CSV to start analysis</p>}
              {messages.map((msg, idx) => (
                msg.role !== 'user' && (
                  <div key={idx} className="message">
                    <div className="message-role">📍 {msg.role.toUpperCase()}</div>
                    <div className="message-content">{msg.content}</div>
                  </div>
                )
              ))}
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
                    <strong>Dataset Processed ✅</strong><br/>
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
        <p>⚡ Pure LangGraph State Machine • No FastAPI • Local Ollama</p>
      </footer>
    </div>
  )
}

export default App
