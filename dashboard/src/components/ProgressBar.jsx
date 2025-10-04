import React from 'react'

function ProgressBar({ progress = 0 }) {
  const percentage = Math.min(100, Math.max(0, progress))

  return (
    <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
      <div
        className="bg-primary-500 h-full transition-all duration-300 ease-out"
        style={{ width: `${percentage}%` }}
      />
    </div>
  )
}

export default ProgressBar
