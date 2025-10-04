import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Calendar, BarChart3, ListTodo, Film } from 'lucide-react'

const navigation = [
  { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { name: 'Jobs', to: '/jobs', icon: ListTodo },
  { name: 'Calendar', to: '/calendar', icon: Calendar },
  { name: 'Analytics', to: '/analytics', icon: BarChart3 },
]

function Sidebar() {
  return (
    <div className="w-64 bg-gray-900 border-r border-gray-700">
      <div className="flex items-center justify-center h-16 border-b border-gray-700">
        <Film className="w-8 h-8 text-primary-500 mr-2" />
        <h1 className="text-xl font-bold text-white">DOPPELGANGER</h1>
      </div>
      
      <nav className="mt-6 px-4">
        <div className="space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <item.icon className="w-5 h-5 mr-3" />
              {item.name}
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
        <div className="text-xs text-gray-500 text-center">
          <p>DOPPELGANGER STUDIO</p>
          <p className="mt-1">v1.0.0</p>
        </div>
      </div>
    </div>
  )
}

export default Sidebar
