import apiClient from './client'

export const calendarApi = {
  /**
   * Reserve a calendar slot
   */
  reserveSlot: async (slotData) => {
    const response = await apiClient.post('/api/calendar/slots', slotData)
    return response.data
  },

  /**
   * Get day view for a specific date
   */
  getDayView: async (date) => {
    const dateStr = typeof date === 'string' ? date : date.toISOString().split('T')[0]
    const response = await apiClient.get(`/api/calendar/day/${dateStr}`)
    return response.data
  },

  /**
   * Get week view starting from a specific date
   */
  getWeekView: async (date) => {
    const dateStr = typeof date === 'string' ? date : date.toISOString().split('T')[0]
    const response = await apiClient.get(`/api/calendar/week/${dateStr}`)
    return response.data
  },

  /**
   * Get optimal slot suggestions
   */
  getSuggestions: async (count = 5) => {
    const response = await apiClient.get('/api/calendar/suggestions', {
      params: { count }
    })
    return response.data
  },

  /**
   * Detect calendar conflicts
   */
  getConflicts: async () => {
    const response = await apiClient.get('/api/calendar/conflicts')
    return response.data
  },
}

export default calendarApi
