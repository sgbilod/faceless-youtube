# DOPPELGANGER STUDIO - Web Dashboard

A modern, real-time web interface for managing the DOPPELGANGER STUDIO video automation pipeline.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Backend API running on port 8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard will be available at http://localhost:3000

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 📋 Features

### Dashboard
- Real-time job monitoring
- Live statistics (pending, running, completed, failed)
- Quick job scheduling
- WebSocket-powered updates

### Jobs Management
- View all jobs with status filtering
- Pause/Resume/Cancel actions
- Real-time progress tracking
- Job details and error reporting

### Calendar View
- Week-based calendar navigation
- Scheduled slot visualization
- Conflict detection
- Today/Previous/Next navigation

### Analytics
- Job status distribution (pie chart)
- Jobs per day (bar chart)
- Completion trends (line chart)
- System metrics and statistics

## 🏗️ Architecture

### Technology Stack
- **React 18.2** - UI framework
- **Vite 5.0** - Build tool and dev server
- **TailwindCSS 3.3** - Utility-first styling
- **React Query 5.14** - Data fetching and caching
- **Recharts 2.10** - Analytics charts
- **Axios 1.6** - HTTP client
- **React Router 6.20** - Client-side routing
- **Zustand 4.4** - State management

### Project Structure
```
src/
├── api/              # API clients (jobs, recurring, calendar, WebSocket)
├── components/       # Reusable UI components
├── pages/            # Page components (Dashboard, Jobs, Calendar, Analytics)
├── hooks/            # Custom React hooks
├── utils/            # Utility functions (date, status)
├── App.jsx           # Main app with routing
└── main.jsx          # React entry point
```

## 🔌 API Integration

### REST API Endpoints
- Job Management: `/api/jobs/*`
- Recurring Schedules: `/api/recurring/*`
- Calendar: `/api/calendar/*`
- Statistics: `/api/statistics`

### WebSocket
- Real-time updates: `ws://localhost:8000/ws`
- Automatic reconnection with exponential backoff
- Event-based job updates

## 🎨 Customization

### Theme Configuration
Edit `tailwind.config.js` to customize colors, spacing, and animations:

```javascript
theme: {
  extend: {
    colors: {
      primary: { /* Your colors */ },
    },
  },
}
```

### Environment Variables
Create `.env` file:

```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## 📚 Documentation

See [WEB_DASHBOARD.md](../docs/WEB_DASHBOARD.md) for comprehensive documentation including:
- Detailed API documentation
- Component usage guides
- Development tips
- Deployment instructions
- Troubleshooting

## 🧪 Development

### Hot Module Replacement
Vite provides instant HMR - changes reflect immediately without full reload.

### Linting
```bash
npm run lint
```

### Formatting
```bash
npm run format
```

## 🐛 Troubleshooting

### Backend Connection Issues
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check CORS configuration
3. Verify Vite proxy settings

### WebSocket Issues
1. Check WebSocket endpoint accessibility
2. Verify firewall settings
3. Check browser console for errors

## 📦 Dependencies

### Production
- React ecosystem (React, React DOM, React Router)
- Data fetching (Axios, React Query)
- UI components (Lucide React for icons)
- Charts (Recharts)
- Utilities (date-fns, Zustand, React Hot Toast)

### Development
- Vite (build tool)
- TailwindCSS (styling)
- ESLint (linting)
- Prettier (formatting)

## 🔐 Security

For production deployment:
1. Update CORS configuration to specific domains
2. Add authentication middleware
3. Use HTTPS for API and WebSocket
4. Implement rate limiting
5. Add input validation

## 📄 License

Part of DOPPELGANGER STUDIO - All Rights Reserved

---

**Version:** 1.0.0  
**Built with:** ❤️ and React  
**For:** DOPPELGANGER STUDIO
