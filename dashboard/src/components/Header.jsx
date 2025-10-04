import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Activity, Clock, CheckCircle, XCircle } from 'lucide-react'
import { statisticsApi } from '../api/statistics'
import useWebSocket from '../hooks/useWebSocket'

function Header() {
  const { isConnected } = useWebSocket()
  
  const { data: stats } = useQuery({
    queryKey: ['statistics'],
    queryFn: statisticsApi.getStatistics,
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  return (
    <header className="h-16 bg-gray-900 border-b border-gray-700 flex items-center justify-between px-6">
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-400">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2 text-gray-300">
          <Activity className="w-4 h-4" />
          <span className="text-sm">
            {stats?.active_jobs || 0} Active
          </span>
        </div>

        <div className="flex items-center space-x-2 text-yellow-400">
          <Clock className="w-4 h-4" />
          <span className="text-sm">
            {stats?.pending_jobs || 0} Pending
          </span>
        </div>

        <div className="flex items-center space-x-2 text-green-400">
          <CheckCircle className="w-4 h-4" />
          <span className="text-sm">
            {stats?.completed_jobs || 0} Completed
          </span>
        </div>

        <div className="flex items-center space-x-2 text-red-400">
          <XCircle className="w-4 h-4" />
          <span className="text-sm">
            {stats?.failed_jobs || 0} Failed
          </span>
        </div>
      </div>
    </header>
  )
}

export default Header
