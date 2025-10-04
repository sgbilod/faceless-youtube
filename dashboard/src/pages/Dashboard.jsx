import React, { useState, useEffect } from 'react'
import { Plus } from 'lucide-react'
import { useJobs } from '../hooks/useJobs'
import useWebSocket from '../hooks/useWebSocket'
import Loading from '../components/Loading'
import JobList from '../components/JobList'
import StatCard from '../components/StatCard'
import CreateJobModal from '../components/CreateJobModal'

function Dashboard() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const { data: jobs, isLoading, refetch } = useJobs()
  const { subscribe } = useWebSocket()

  // Subscribe to job updates via WebSocket
  useEffect(() => {
    const unsubscribe = subscribe('job_update', () => {
      refetch()
    })

    return unsubscribe
  }, [subscribe, refetch])

  if (isLoading) {
    return <Loading message="Loading dashboard..." />
  }

  const stats = {
    total: jobs?.length || 0,
    pending: jobs?.filter(j => j.status === 'pending').length || 0,
    running: jobs?.filter(j => j.status === 'running').length || 0,
    completed: jobs?.filter(j => j.status === 'completed').length || 0,
    failed: jobs?.filter(j => j.status === 'failed').length || 0,
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
        >
          <Plus className="w-5 h-5 mr-2" />
          Schedule Video
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Jobs"
          value={stats.total}
          color="blue"
        />
        <StatCard
          title="Pending"
          value={stats.pending}
          color="yellow"
        />
        <StatCard
          title="Running"
          value={stats.running}
          color="blue"
          animated
        />
        <StatCard
          title="Completed"
          value={stats.completed}
          color="green"
        />
      </div>

      <div className="bg-gray-900 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Recent Jobs</h2>
        <JobList jobs={jobs || []} />
      </div>

      <CreateJobModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  )
}

export default Dashboard
