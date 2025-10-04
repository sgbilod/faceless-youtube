import React from 'react'
import { Loader2 } from 'lucide-react'

function Loading({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center h-64">
      <Loader2 className="w-12 h-12 text-primary-500 animate-spin mb-4" />
      <p className="text-gray-400">{message}</p>
    </div>
  )
}

export default Loading
