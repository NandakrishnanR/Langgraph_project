import './AgentProgress.css'

const statusConfig = {
  'completed': { color: '#10b981', label: 'Completed' },
  'in-progress': { color: '#f59e0b', label: 'Processing' },
  'pending': { color: '#6b7280', label: 'Pending' },
  'failed': { color: '#ef4444', label: 'Failed' }
}

export default function AgentProgress({ agents }) {
  return (
    <div className="agent-progress">
      <h3 className="progress-title">Analysis Pipeline</h3>
      <div className="agents-grid">
        {agents.map((agent, idx) => {
          const config = statusConfig[agent.status] || statusConfig.pending
          return (
            <div key={idx} className={`agent-card agent-${agent.status}`}>
              <div className="agent-info">
                <h4 className="agent-name">{agent.name}</h4>
                <p className="agent-status">{config.label}</p>
                <p className="agent-time">{agent.time}</p>
              </div>
            </div>
          )
        })}
      </div>
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{
            width: `${(agents.filter(a => a.status === 'completed').length / agents.length) * 100}%`
          }}
        ></div>
      </div>
    </div>
  )
}
