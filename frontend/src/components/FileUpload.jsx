import { useRef } from 'react'
import './FileUpload.css'

export default function FileUpload({ onFileSelected, analyzing }) {
  const fileInput = useRef(null)

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      onFileSelected(file)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    const file = e.dataTransfer.files?.[0]
    if (file?.name.endsWith('.csv')) {
      onFileSelected(file)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  return (
    <div className="file-upload-wrapper">
      <div
        className="file-upload-zone"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        style={{ opacity: analyzing ? 0.6 : 1, pointerEvents: analyzing ? 'none' : 'auto' }}
      >
        <h2>Upload Your Dataset</h2>
        <p className="upload-text">Drag and drop your CSV file here, or click to browse</p>
        <input
          ref={fileInput}
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          disabled={analyzing}
          className="file-input"
        />
        <button
          className="browse-btn"
          onClick={() => fileInput.current?.click()}
          disabled={analyzing}
        >
          {analyzing ? 'Analyzing...' : 'Choose File'}
        </button>
      </div>
      <div className="upload-info">
        <p>CSV files supported</p>
        <p>Instant analysis</p>
        <p>Algorithm recommendations</p>
      </div>
    </div>
  )
}
