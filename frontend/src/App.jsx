import { useState } from 'react'
import axios from 'axios'
import './App.css'
import FileUpload from './components/FileUpload'
import ResultsCard from './components/ResultsCard'
import AgentProgress from './components/AgentProgress'
import CodeDisplay from './components/CodeDisplay'

function App() {
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [agents, setAgents] = useState([])

  const handleFileSelected = async (file) => {
    if (!file) return

    setAnalyzing(true)
    setError(null)
    setAgents([
      { name: 'DataAnalyzer', status: 'in-progress', time: '0.2s' },
      { name: 'ProblemAnalyzer', status: 'pending', time: '0.3s' },
      { name: 'AlgorithmSelector', status: 'pending', time: '0.2s' },
      { name: 'CodeGenerator', status: 'pending', time: '0.4s' }
    ])

    try {
      const formData = new FormData()
      formData.append('file', file)

      // Simulate agent progression
      setTimeout(() => updateAgentStatus(1), 800)
      setTimeout(() => updateAgentStatus(2), 1600)
      setTimeout(() => updateAgentStatus(3), 2400)

      const response = await axios.post('/api/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      setResult(response.data)
      setAgents(prev =>
        prev.map((agent, idx) => ({
          ...agent,
          status: 'completed'
        }))
      )
    } catch (err) {
      setError(err.response?.data?.message || 'Analysis failed. Please try again.')
      setAgents(prev =>
        prev.map(agent => ({
          ...agent,
          status: 'failed'
        }))
      )
    } finally {
      setAnalyzing(false)
    }
  }

  const updateAgentStatus = (index) => {
    setAgents(prev => {
      const newAgents = [...prev]
      if (index > 0) newAgents[index - 1].status = 'completed'
      if (index < newAgents.length) newAgents[index].status = 'in-progress'
      return newAgents
    })
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1 className="title">LangGraph</h1>
          <p className="subtitle">Intelligent ML Solution Advisor</p>
          <p className="description">Upload your dataset and get AI-powered algorithm recommendations</p>
        </div>
      </header>

      <div className="container">
        <div className="main-grid">
          {/* File Upload Section */}
          <div className="upload-section">
            <FileUpload onFileSelected={handleFileSelected} analyzing={analyzing} />
          </div>

          {/* Agent Progress */}
          {agents.length > 0 && <AgentProgress agents={agents} />}

          {/* Error Display */}
          {error && (
            <div className="error-card">
              <div className="error-message">{error}</div>
            </div>
          )}

          {/* Results Section */}
          {result && (
            <>
              <ResultsCard result={result} />
              <CodeDisplay code={result.code} />
            </>
          )}
        </div>
      </div>

      <footer className="footer">
        <p>LangGraph – Smart ML Advisor</p>
      </footer>
    </div>
  )
}

export default App
