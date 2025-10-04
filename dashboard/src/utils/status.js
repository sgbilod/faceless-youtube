export function getStatusColor(status) {
  const colors = {
    pending: 'yellow',
    running: 'blue',
    completed: 'green',
    failed: 'red',
    cancelled: 'gray',
    paused: 'orange',
  }
  
  return colors[status] || 'gray'
}

export function getStatusIcon(status) {
  const icons = {
    pending: 'Clock',
    running: 'Activity',
    completed: 'CheckCircle',
    failed: 'XCircle',
    cancelled: 'Ban',
    paused: 'Pause',
  }
  
  return icons[status] || 'Circle'
}

export function getStatusText(status) {
  return status.charAt(0).toUpperCase() + status.slice(1)
}
