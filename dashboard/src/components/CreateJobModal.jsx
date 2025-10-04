import React, { useState } from 'react'
import { X } from 'lucide-react'
import { useScheduleJob } from '../hooks/useJobs'

function CreateJobModal({ isOpen, onClose }) {
  const [formData, setFormData] = useState({
    show_name: '',
    episode_number: 1,
    scheduled_time: '',
    topic: '',
    duration: 60,
    priority: 1,
  })

  const scheduleMutation = useScheduleJob()

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      await scheduleMutation.mutateAsync(formData)
      onClose()
      setFormData({
        show_name: '',
        episode_number: 1,
        scheduled_time: '',
        topic: '',
        duration: 60,
        priority: 1,
      })
    } catch (error) {
      console.error('Failed to schedule job:', error)
    }
  }

  const handleChange = (e) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) : value,
    }))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-gray-900 rounded-lg w-full max-w-2xl p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Schedule New Video</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Show Name
            </label>
            <input
              type="text"
              name="show_name"
              value={formData.show_name}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
              placeholder="e.g., I Love Luna"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Episode Number
              </label>
              <input
                type="number"
                name="episode_number"
                value={formData.episode_number}
                onChange={handleChange}
                min="1"
                required
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Duration (seconds)
              </label>
              <input
                type="number"
                name="duration"
                value={formData.duration}
                onChange={handleChange}
                min="30"
                max="600"
                required
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Topic (Optional)
            </label>
            <input
              type="text"
              name="topic"
              value={formData.topic}
              onChange={handleChange}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
              placeholder="e.g., Luna tries to start a space tourism business"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Scheduled Time (Optional)
            </label>
            <input
              type="datetime-local"
              name="scheduled_time"
              value={formData.scheduled_time}
              onChange={handleChange}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Leave empty to start immediately
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Priority
            </label>
            <select
              name="priority"
              value={formData.priority}
              onChange={handleChange}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
            >
              <option value="1">Low</option>
              <option value="2">Normal</option>
              <option value="3">High</option>
            </select>
          </div>

          <div className="flex justify-end space-x-4 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={scheduleMutation.isPending}
              className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {scheduleMutation.isPending ? 'Scheduling...' : 'Schedule Video'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateJobModal
