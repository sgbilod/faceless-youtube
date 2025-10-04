import React from 'react'
import { Activity, Clock, CheckCircle, TrendingUp } from 'lucide-react'

const iconMap = {
  blue: Activity,
  yellow: Clock,
  green: CheckCircle,
  purple: TrendingUp,
}

const colorMap = {
  blue: 'bg-blue-500',
  yellow: 'bg-yellow-500',
  green: 'bg-green-500',
  purple: 'bg-purple-500',
}

function StatCard({ title, value, color = 'blue', animated = false }) {
  const Icon = iconMap[color]
  const bgColor = colorMap[color]

  return (
    <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-white mt-2">{value}</p>
        </div>
        <div className={`${bgColor} p-3 rounded-lg ${animated ? 'animate-pulse' : ''}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  )
}

export default StatCard
