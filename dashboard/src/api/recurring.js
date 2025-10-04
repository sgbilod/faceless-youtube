import apiClient from './client'

export const recurringApi = {
  /**
   * Create a new recurring schedule
   */
  createRecurring: async (scheduleData) => {
    const response = await apiClient.post('/api/recurring/create', scheduleData)
    return response.data
  },

  /**
   * Get all recurring schedules
   */
  getRecurring: async () => {
    const response = await apiClient.get('/api/recurring')
    return response.data
  },

  /**
   * Pause a recurring schedule
   */
  pauseRecurring: async (jobId) => {
    const response = await apiClient.post(`/api/recurring/${jobId}/pause`)
    return response.data
  },

  /**
   * Resume a recurring schedule
   */
  resumeRecurring: async (jobId) => {
    const response = await apiClient.post(`/api/recurring/${jobId}/resume`)
    return response.data
  },

  /**
   * Delete a recurring schedule
   */
  deleteRecurring: async (jobId) => {
    const response = await apiClient.delete(`/api/recurring/${jobId}`)
    return response.data
  },
}

export default recurringApi
