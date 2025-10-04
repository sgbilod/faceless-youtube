import apiClient from './client'

export const statisticsApi = {
  /**
   * Get system statistics
   */
  getStatistics: async () => {
    const response = await apiClient.get('/api/statistics')
    return response.data
  },

  /**
   * Get health status
   */
  getHealth: async () => {
    const response = await apiClient.get('/api/health', { silent: true })
    return response.data
  },
}

export default statisticsApi
