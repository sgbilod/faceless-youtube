import React from 'react'
import { Play, Pause, X, Clock, Activity, CheckCircle, XCircle, Ban } from 'lucide-react'
import { useCancelJob, usePauseJob, useResumeJob } from '../hooks/useJobs'
import { formatDate, formatRelativeTime } from '../utils/date'
import { getStatusColor } from '../utils/status'
import ProgressBar from './ProgressBar'

const statusIcons = {
  pending: Clock,
  running: Activity,
  completed: CheckCircle,
  failed: XCircle,
  cancelled: Ban,
  paused: Pause,
}

function JobCard({ job }) {
  const cancelMutation = useCancelJob()
  const pauseMutation = usePauseJob()
  const resumeMutation = useResumeJob()

  const StatusIcon = statusIcons[job.status] || Activity
  const statusColor = getStatusColor(job.status)

  const handleCancel = () => {
    if (confirm('Are you sure you want to cancel this job?')) {
      cancelMutation.mutate(job.job_id)
    }
  }

  const handlePause = () => {
    pauseMutation.mutate(job.job_id)
  }

  const handleResume = () => {
    resumeMutation.mutate(job.job_id)
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start space-x-3">
          <div className={`p-2 rounded-lg bg-${statusColor}-500 bg-opacity-20`}>
            <StatusIcon className={`w-5 h-5 text-${statusColor}-500`} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">{job.job_id}</h3>
            <p className="text-sm text-gray-400 mt-1">
              {job.show_name || 'Untitled'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {formatRelativeTime(job.created_at)}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {job.status === 'running' && (
            <button
              onClick={handlePause}
              className="p-2 text-yellow-500 hover:bg-gray-700 rounded-lg transition-colors"
              title="Pause"
            >
              <Pause className="w-4 h-4" />
            </button>
          )}
          {job.status === 'paused' && (
            <button
              onClick={handleResume}
              className="p-2 text-green-500 hover:bg-gray-700 rounded-lg transition-colors"
              title="Resume"
            >
              <Play className="w-4 h-4" />
            </button>
          )}
          {(job.status === 'pending' || job.status === 'running' || job.status === 'paused') && (
            <button
              onClick={handleCancel}
              className="p-2 text-red-500 hover:bg-gray-700 rounded-lg transition-colors"
              title="Cancel"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {job.progress !== undefined && job.status === 'running' && (
        <div className="mb-4">
          <ProgressBar progress={job.progress} />
          <p className="text-xs text-gray-400 mt-1">
            {Math.round(job.progress)}% complete
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-400">Status</p>
          <p className="text-white font-medium capitalize">{job.status}</p>
        </div>
        <div>
          <p className="text-gray-400">Scheduled For</p>
          <p className="text-white font-medium">
            {job.scheduled_time ? formatDate(job.scheduled_time) : 'Immediate'}
          </p>
        </div>
      </div>

      {job.error && (
        <div className="mt-4 p-3 bg-red-500 bg-opacity-10 border border-red-500 rounded-lg">
          <p className="text-sm text-red-400">{job.error}</p>
        </div>
      )}
    </div>
  )
}

export default JobCard
