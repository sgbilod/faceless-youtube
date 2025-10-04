import apiClient from './client'

export const jobsApi = {
  /**
   * Schedule a new video job
   */
  scheduleJob: async (jobData) => {
    const response = await apiClient.post('/api/jobs/schedule', jobData)
    return response.data
  },

  /**
   * Get all jobs with optional status filter
   */
  getJobs: async (status = null) => {
    const params = status ? { status } : {}
    const response = await apiClient.get('/api/jobs', { params })
    return response.data
  },

  /**
   * Get a specific job by ID
   */
  getJob: async (jobId) => {
    const response = await apiClient.get(`/api/jobs/${jobId}`)
    return response.data
  },

  /**
   * Cancel a job
   */
  cancelJob: async (jobId) => {
    const response = await apiClient.post(`/api/jobs/${jobId}/cancel`)
    return response.data
  },

  /**
   * Pause a job
   */
  pauseJob: async (jobId) => {
    const response = await apiClient.post(`/api/jobs/${jobId}/pause`)
    return response.data
  },

  /**
   * Resume a job
   */
  resumeJob: async (jobId) => {
    const response = await apiClient.post(`/api/jobs/${jobId}/resume`)
    return response.data
  },
}

export default jobsApi
