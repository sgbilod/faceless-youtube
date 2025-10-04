import React, { useState } from 'react'
import { Filter } from 'lucide-react'
import { useJobs } from '../hooks/useJobs'
import Loading from '../components/Loading'
import JobList from '../components/JobList'

const statusOptions = [
  { value: null, label: 'All Jobs' },
  { value: 'pending', label: 'Pending' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
]

function Jobs() {
  const [statusFilter, setStatusFilter] = useState(null)
  const { data: jobs, isLoading } = useJobs(statusFilter)

  if (isLoading) {
    return <Loading message="Loading jobs..." />
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">All Jobs</h1>
        
        <div className="flex items-center space-x-2">
          <Filter className="w-5 h-5 text-gray-400" />
          <select
            value={statusFilter || ''}
            onChange={(e) => setStatusFilter(e.target.value || null)}
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
          >
            {statusOptions.map((option) => (
              <option key={option.value || 'all'} value={option.value || ''}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-gray-900 rounded-lg p-6">
        <JobList jobs={jobs || []} />
      </div>
    </div>
  )
}

export default Jobs
