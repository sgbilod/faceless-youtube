import { format, formatDistance, parseISO } from 'date-fns'

export function formatDate(date) {
  if (!date) return 'N/A'
  
  try {
    const parsedDate = typeof date === 'string' ? parseISO(date) : date
    return format(parsedDate, 'MMM d, yyyy HH:mm')
  } catch (error) {
    console.error('Error formatting date:', error)
    return 'Invalid date'
  }
}

export function formatRelativeTime(date) {
  if (!date) return 'N/A'
  
  try {
    const parsedDate = typeof date === 'string' ? parseISO(date) : date
    return formatDistance(parsedDate, new Date(), { addSuffix: true })
  } catch (error) {
    console.error('Error formatting relative time:', error)
    return 'Invalid date'
  }
}

export function formatDuration(seconds) {
  if (!seconds) return '0s'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  const parts = []
  if (hours > 0) parts.push(`${hours}h`)
  if (minutes > 0) parts.push(`${minutes}m`)
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`)
  
  return parts.join(' ')
}
