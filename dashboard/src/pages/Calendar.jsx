import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react'
import { calendarApi } from '../api/calendar'
import { formatDate } from '../utils/date'
import Loading from '../components/Loading'

function Calendar() {
  const [currentDate, setCurrentDate] = useState(new Date())
  
  const dateStr = currentDate.toISOString().split('T')[0]

  const { data: weekData, isLoading } = useQuery({
    queryKey: ['calendar', 'week', dateStr],
    queryFn: () => calendarApi.getWeekView(dateStr),
  })

  const { data: conflicts } = useQuery({
    queryKey: ['calendar', 'conflicts'],
    queryFn: calendarApi.getConflicts,
    refetchInterval: 60000, // Refetch every minute
  })

  const goToPreviousWeek = () => {
    const newDate = new Date(currentDate)
    newDate.setDate(newDate.getDate() - 7)
    setCurrentDate(newDate)
  }

  const goToNextWeek = () => {
    const newDate = new Date(currentDate)
    newDate.setDate(newDate.getDate() + 7)
    setCurrentDate(newDate)
  }

  const goToToday = () => {
    setCurrentDate(new Date())
  }

  if (isLoading) {
    return <Loading message="Loading calendar..." />
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Calendar</h1>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={goToToday}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            Today
          </button>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={goToPreviousWeek}
              className="p-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <span className="text-white font-medium px-4">
              {formatDate(currentDate)}
            </span>
            <button
              onClick={goToNextWeek}
              className="p-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {conflicts && conflicts.length > 0 && (
        <div className="bg-red-500 bg-opacity-10 border border-red-500 rounded-lg p-4">
          <div className="flex items-center space-x-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">
              {conflicts.length} conflict{conflicts.length !== 1 ? 's' : ''} detected
            </span>
          </div>
        </div>
      )}

      <div className="bg-gray-900 rounded-lg p-6">
        {weekData && weekData.length > 0 ? (
          <div className="space-y-4">
            {weekData.map((day) => (
              <div key={day.date} className="border-b border-gray-700 pb-4 last:border-0">
                <h3 className="text-lg font-semibold text-white mb-3">
                  {new Date(day.date).toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </h3>
                
                {day.slots && day.slots.length > 0 ? (
                  <div className="space-y-2">
                    {day.slots.map((slot, index) => (
                      <div
                        key={index}
                        className="bg-gray-800 rounded-lg p-4 border border-gray-700"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="text-white font-medium">
                              {slot.job_id || 'Reserved Slot'}
                            </p>
                            <p className="text-sm text-gray-400 mt-1">
                              {new Date(slot.start_time).toLocaleTimeString()} - 
                              {new Date(slot.end_time).toLocaleTimeString()}
                            </p>
                          </div>
                          {slot.status && (
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                              slot.status === 'reserved' ? 'bg-blue-500 text-white' :
                              slot.status === 'completed' ? 'bg-green-500 text-white' :
                              'bg-gray-600 text-white'
                            }`}>
                              {slot.status}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No slots scheduled</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <p>No calendar data available for this week</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Calendar
