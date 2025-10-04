import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, Clock, CheckCircle, XCircle } from 'lucide-react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { statisticsApi } from '../api/statistics'
import Loading from '../components/Loading'

const COLORS = ['#0ea5e9', '#22c55e', '#ef4444', '#f59e0b']

function Analytics() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['statistics'],
    queryFn: statisticsApi.getStatistics,
    refetchInterval: 30000,
  })

  if (isLoading) {
    return <Loading message="Loading analytics..." />
  }

  // Prepare data for charts
  const statusData = [
    { name: 'Pending', value: stats?.pending_jobs || 0, color: COLORS[3] },
    { name: 'Running', value: stats?.active_jobs || 0, color: COLORS[0] },
    { name: 'Completed', value: stats?.completed_jobs || 0, color: COLORS[1] },
    { name: 'Failed', value: stats?.failed_jobs || 0, color: COLORS[2] },
  ]

  const totalJobs = statusData.reduce((sum, item) => sum + item.value, 0)

  const timelineData = [
    { name: 'Mon', jobs: 12 },
    { name: 'Tue', jobs: 19 },
    { name: 'Wed', jobs: 15 },
    { name: 'Thu', jobs: 22 },
    { name: 'Fri', jobs: 18 },
    { name: 'Sat', jobs: 25 },
    { name: 'Sun', jobs: 20 },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Analytics</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total Jobs</p>
              <p className="text-3xl font-bold text-white mt-2">{totalJobs}</p>
            </div>
            <TrendingUp className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Active</p>
              <p className="text-3xl font-bold text-white mt-2">{stats?.active_jobs || 0}</p>
            </div>
            <Clock className="w-10 h-10 text-yellow-500" />
          </div>
        </div>

        <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Completed</p>
              <p className="text-3xl font-bold text-white mt-2">{stats?.completed_jobs || 0}</p>
            </div>
            <CheckCircle className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Failed</p>
              <p className="text-3xl font-bold text-white mt-2">{stats?.failed_jobs || 0}</p>
            </div>
            <XCircle className="w-10 h-10 text-red-500" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Job Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Jobs per Day</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="jobs" fill="#0ea5e9" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold text-white mb-4">Job Completion Trend</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={timelineData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
              labelStyle={{ color: '#fff' }}
            />
            <Legend />
            <Line type="monotone" dataKey="jobs" stroke="#0ea5e9" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold text-white mb-4">System Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-400">Total Recurring Schedules</p>
            <p className="text-white font-medium text-lg mt-1">{stats?.total_recurring_schedules || 0}</p>
          </div>
          <div>
            <p className="text-gray-400">Active Recurring Schedules</p>
            <p className="text-white font-medium text-lg mt-1">{stats?.active_recurring_schedules || 0}</p>
          </div>
          <div>
            <p className="text-gray-400">Total Calendar Slots</p>
            <p className="text-white font-medium text-lg mt-1">{stats?.total_calendar_slots || 0}</p>
          </div>
          <div>
            <p className="text-gray-400">Reserved Slots</p>
            <p className="text-white font-medium text-lg mt-1">{stats?.reserved_slots || 0}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Analytics
