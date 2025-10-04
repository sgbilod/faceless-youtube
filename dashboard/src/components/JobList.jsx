import React from 'react'
import JobCard from './JobCard'

function JobList({ jobs }) {
  if (!jobs || jobs.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p>No jobs found</p>
      </div>
    )
  }

  // Sort jobs by created_at (most recent first)
  const sortedJobs = [...jobs].sort((a, b) => {
    return new Date(b.created_at) - new Date(a.created_at)
  })

  return (
    <div className="space-y-4">
      {sortedJobs.map((job) => (
        <JobCard key={job.job_id} job={job} />
      ))}
    </div>
  )
}

export default JobList
