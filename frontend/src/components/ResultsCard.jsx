import './ResultsCard.css'

export default function ResultsCard({ result }) {
  return (
    <div className="results-wrapper">
      {/* Algorithm Section */}
      <div className="algorithm-card">
        <div className="algorithm-header">
          <h2>Recommended Algorithm</h2>
          <span className="algorithm-badge">{result.algorithm}</span>
        </div>
        <p className="algorithm-reason">{result.reason}</p>
      </div>

      {/* Data Summary */}
      <div className="data-summary-card">
        <h3>Dataset Analysis</h3>
        <pre className="summary-text">{result.data_summary}</pre>
      </div>

      {/* Agents Info */}
      {result.agents && (
        <div className="agents-summary">
          <h3>Analysis Agents</h3>
          <div className="agents-list">
            {result.agents.map((agent, idx) => (
              <div key={idx} className="agent-item">
                <div>
                  <strong>{agent.name}</strong>
                  <small>{agent.time}</small>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
