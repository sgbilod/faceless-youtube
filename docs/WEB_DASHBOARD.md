# Web Dashboard Documentation

## Overview

The DOPPELGANGER STUDIO Web Dashboard provides a comprehensive web interface for managing the entire video automation pipeline. Built with React and FastAPI, it offers real-time monitoring, job management, scheduling, and analytics.

## Architecture

### Backend (FastAPI)

**Location:** `src/api/main.py`

The FastAPI backend provides a REST API and WebSocket server for real-time updates.

#### Key Features

- **REST API**: 20+ endpoints for full system control
- **WebSocket**: Real-time job progress updates
- **CORS**: Configured for React development servers
- **Background Monitoring**: Continuous job status tracking
- **Integration**: Direct access to all scheduler components

#### API Endpoints

##### Health Check
- `GET /api/health` - System health and scheduler status

##### Job Management
- `POST /api/jobs/schedule` - Schedule a new video job
- `GET /api/jobs` - List all jobs (optional status filter)
- `GET /api/jobs/{job_id}` - Get specific job details
- `POST /api/jobs/{job_id}/cancel` - Cancel a job
- `POST /api/jobs/{job_id}/pause` - Pause a running job
- `POST /api/jobs/{job_id}/resume` - Resume a paused job

##### Recurring Schedules
- `POST /api/recurring/create` - Create recurring schedule (daily/weekly/monthly)
- `GET /api/recurring` - List all recurring schedules
- `POST /api/recurring/{job_id}/pause` - Pause recurring schedule
- `POST /api/recurring/{job_id}/resume` - Resume recurring schedule
- `DELETE /api/recurring/{job_id}` - Delete recurring schedule

##### Calendar Management
- `POST /api/calendar/slots` - Reserve a calendar slot
- `GET /api/calendar/day/{date}` - Get day view (YYYY-MM-DD)
- `GET /api/calendar/week/{date}` - Get week view starting from date
- `GET /api/calendar/suggestions` - Get optimal time slot suggestions
- `GET /api/calendar/conflicts` - Detect scheduling conflicts

##### Statistics
- `GET /api/statistics` - System statistics and metrics

##### Real-time Updates
- `WebSocket /ws` - Real-time job updates and notifications

#### WebSocket Events

The WebSocket connection broadcasts the following event types:

- `job_created` - New job scheduled
- `job_cancelled` - Job cancelled
- `job_paused` - Job paused
- `job_resumed` - Job resumed
- `job_update` - Job progress update (every 5 seconds)
- `connection` - Connection status change

### Frontend (React)

**Location:** `dashboard/src/`

The React frontend provides an intuitive, real-time dashboard for system management.

#### Technology Stack

- **React 18.2** - UI framework
- **React Router 6.20** - Client-side routing
- **TailwindCSS 3.3** - Utility-first styling
- **React Query 5.14** - Data fetching and caching
- **Recharts 2.10** - Analytics charts
- **Axios 1.6** - HTTP client
- **Zustand 4.4** - State management
- **date-fns 3.0** - Date utilities
- **Lucide React 0.294** - Icons
- **React Hot Toast 2.4** - Notifications

#### Project Structure

```
dashboard/
├── src/
│   ├── api/              # API clients
│   │   ├── client.js     # Axios instance
│   │   ├── jobs.js       # Job endpoints
│   │   ├── recurring.js  # Recurring endpoints
│   │   ├── calendar.js   # Calendar endpoints
│   │   ├── statistics.js # Statistics endpoints
│   │   └── websocket.js  # WebSocket client
│   │
│   ├── components/       # Reusable components
│   │   ├── Layout.jsx    # Main layout
│   │   ├── Sidebar.jsx   # Navigation sidebar
│   │   ├── Header.jsx    # Top header with stats
│   │   ├── JobList.jsx   # Job list component
│   │   ├── JobCard.jsx   # Individual job card
│   │   ├── StatCard.jsx  # Statistics card
│   │   ├── ProgressBar.jsx # Progress indicator
│   │   ├── CreateJobModal.jsx # Job creation modal
│   │   └── Loading.jsx   # Loading spinner
│   │
│   ├── pages/            # Page components
│   │   ├── Dashboard.jsx # Main dashboard
│   │   ├── Jobs.jsx      # Jobs management
│   │   ├── Calendar.jsx  # Calendar view
│   │   └── Analytics.jsx # Analytics dashboard
│   │
│   ├── hooks/            # Custom React hooks
│   │   ├── useJobs.js    # Job management hooks
│   │   └── useWebSocket.js # WebSocket hook
│   │
│   ├── utils/            # Utility functions
│   │   ├── date.js       # Date formatting
│   │   └── status.js     # Status utilities
│   │
│   ├── App.jsx           # Main app component
│   ├── main.jsx          # React entry point
│   └── index.css         # Global styles
│
├── package.json          # Dependencies
├── vite.config.js        # Vite configuration
├── tailwind.config.js    # TailwindCSS config
├── postcss.config.js     # PostCSS config
└── index.html            # HTML entry point
```

## Installation & Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- All Task #9 dependencies installed

### Backend Setup

The FastAPI backend is already integrated into the main project:

```bash
# No additional installation needed
# Backend starts with: uvicorn src.api.main:app --reload
```

### Frontend Setup

1. **Navigate to dashboard directory:**

```bash
cd dashboard
```

2. **Install dependencies:**

```bash
npm install
```

3. **Configure environment (optional):**

Create `.env` file in `dashboard/` directory:

```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## Running the Dashboard

### Development Mode

#### Start Backend (Terminal 1)

```bash
# From project root
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

#### Start Frontend (Terminal 2)

```bash
# From dashboard directory
cd dashboard
npm run dev
```

Frontend will be available at: http://localhost:3000

### Production Build

#### Build Frontend

```bash
cd dashboard
npm run build
```

Built files will be in `dashboard/dist/`

#### Serve Production Build

Option 1 - Use Vite preview:
```bash
npm run preview
```

Option 2 - Serve with FastAPI:
```python
# Add to src/api/main.py
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="dashboard/dist", html=True), name="static")
```

## Features

### 1. Dashboard Page

**Path:** `/dashboard`

**Features:**
- Real-time job statistics
- Recent jobs list
- Quick job scheduling
- WebSocket-powered live updates

**Components:**
- `StatCard` - Displays job statistics (Total, Pending, Running, Completed)
- `JobList` - Shows recent jobs with status
- `CreateJobModal` - Modal for scheduling new videos

### 2. Jobs Page

**Path:** `/jobs`

**Features:**
- View all jobs with filtering
- Filter by status (pending, running, completed, failed, cancelled)
- Real-time job updates
- Job actions (pause, resume, cancel)

**Job Actions:**
- **Pause** - Pause a running job (yellow button)
- **Resume** - Resume a paused job (green button)
- **Cancel** - Cancel pending/running/paused jobs (red button)

### 3. Calendar Page

**Path:** `/calendar`

**Features:**
- Week view of scheduled jobs
- Navigate weeks (previous/next/today)
- Conflict detection
- Slot status indicators

**Slot States:**
- **Reserved** - Slot reserved but job not started (blue)
- **Completed** - Job completed successfully (green)

### 4. Analytics Page

**Path:** `/analytics`

**Features:**
- Job status distribution (pie chart)
- Jobs per day (bar chart)
- Job completion trend (line chart)
- System information panel

**Metrics:**
- Total jobs
- Active jobs
- Completed jobs
- Failed jobs
- Recurring schedules
- Calendar slots

## API Client Usage

### Jobs

```javascript
import { jobsApi } from './api/jobs'

// Schedule a job
const job = await jobsApi.scheduleJob({
  show_name: "I Love Luna",
  episode_number: 1,
  scheduled_time: "2025-06-01T10:00:00",
  topic: "Luna starts a space business",
  duration: 60,
  priority: 2
})

// Get all jobs
const jobs = await jobsApi.getJobs()

// Filter by status
const runningJobs = await jobsApi.getJobs('running')

// Cancel a job
await jobsApi.cancelJob(job.job_id)
```

### React Query Hooks

```javascript
import { useJobs, useScheduleJob, useCancelJob } from './hooks/useJobs'

function MyComponent() {
  // Fetch jobs with automatic caching and refetching
  const { data: jobs, isLoading } = useJobs()

  // Schedule mutation with success handling
  const scheduleMutation = useScheduleJob()
  
  const handleSchedule = async (jobData) => {
    await scheduleMutation.mutateAsync(jobData)
    // Automatically invalidates and refetches jobs
  }

  // Cancel mutation
  const cancelMutation = useCancelJob()
  
  const handleCancel = async (jobId) => {
    await cancelMutation.mutateAsync(jobId)
  }

  return (
    // Component JSX
  )
}
```

### WebSocket Integration

```javascript
import useWebSocket from './hooks/useWebSocket'

function MyComponent() {
  const { isConnected, subscribe } = useWebSocket()

  useEffect(() => {
    // Subscribe to job updates
    const unsubscribe = subscribe('job_update', (data) => {
      console.log('Job updated:', data)
      // Update UI or refetch data
    })

    return unsubscribe // Cleanup on unmount
  }, [subscribe])

  return (
    <div>
      Status: {isConnected ? 'Connected' : 'Disconnected'}
    </div>
  )
}
```

## Styling

### TailwindCSS

The dashboard uses TailwindCSS for styling with a custom theme:

**Color Palette:**
- Primary: Blue shades (#0ea5e9)
- Background: Gray 900/800 (#111827, #1f2937)
- Text: White/Gray variants
- Status colors: Yellow (pending), Blue (running), Green (completed), Red (failed)

**Custom Classes:**

```css
/* Animations */
animate-spin-slow  /* Slow spinning (3s) */
animate-pulse-slow /* Slow pulsing (3s) */

/* Custom scrollbar */
::-webkit-scrollbar        /* 8px width */
::-webkit-scrollbar-track  /* Gray 800 */
::-webkit-scrollbar-thumb  /* Gray 600 */
```

## Error Handling

### API Errors

All API errors are intercepted and displayed as toast notifications:

```javascript
// Automatic error handling
try {
  await jobsApi.scheduleJob(data)
} catch (error) {
  // Error automatically shown via toast
  // error.response.data.detail contains error message
}

// Silent errors (no toast)
const response = await apiClient.get('/endpoint', { silent: true })
```

### WebSocket Reconnection

The WebSocket client automatically reconnects with exponential backoff:

- Max attempts: 5
- Initial delay: 1 second
- Backoff: 2^(attempt - 1) seconds

## Development Tips

### Hot Module Replacement

Vite provides instant HMR for React components. Changes are reflected immediately without full page reload.

### API Proxy

Vite is configured to proxy API requests during development:

```javascript
// vite.config.js
proxy: {
  '/api': 'http://localhost:8000',
  '/ws': {
    target: 'ws://localhost:8000',
    ws: true
  }
}
```

This allows using relative URLs in frontend code:

```javascript
// Works in both development and production
await axios.get('/api/jobs')
```

### React Query DevTools

Add React Query DevTools for debugging:

```bash
npm install @tanstack/react-query-devtools
```

```javascript
// main.jsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

<QueryClientProvider client={queryClient}>
  <App />
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

## Testing

### Manual Testing

1. **Start backend and frontend**
2. **Navigate to http://localhost:3000**
3. **Test job scheduling:**
   - Click "Schedule Video"
   - Fill form and submit
   - Verify job appears in dashboard
4. **Test real-time updates:**
   - Watch job status change automatically
   - Observe progress bar updates
5. **Test job actions:**
   - Pause a running job
   - Resume a paused job
   - Cancel a pending job
6. **Test calendar:**
   - Navigate to Calendar page
   - Check week view displays slots
   - Test navigation (previous/next/today)
7. **Test analytics:**
   - Navigate to Analytics page
   - Verify charts render with data
   - Check statistics accuracy

### Integration Testing

The dashboard integrates with all Task #9 scheduler components:

- `ContentScheduler` - Job scheduling and management
- `JobExecutor` - Job execution and monitoring
- `RecurringScheduler` - Recurring schedule management
- `CalendarManager` - Calendar slot management

Test integration by:
1. Scheduling jobs via dashboard
2. Verifying jobs execute via Task #9 components
3. Checking job status updates in real-time
4. Validating calendar slot reservations

## Performance

### Optimization Techniques

1. **React Query Caching**
   - Automatic request deduplication
   - Stale-while-revalidate strategy
   - Background refetching

2. **Code Splitting**
   - Lazy loading for routes
   - Reduced initial bundle size

3. **WebSocket Efficiency**
   - Single connection for all updates
   - Event-based updates (no polling)
   - Automatic reconnection

4. **Optimistic Updates**
   - Immediate UI feedback
   - Background API calls
   - Rollback on failure

### Bundle Size

Vite automatically optimizes the production bundle:

- Tree shaking removes unused code
- Minification reduces file size
- Code splitting for route-based chunks

## Troubleshooting

### Backend Connection Issues

**Problem:** Frontend can't connect to backend

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check CORS configuration in `src/api/main.py`
3. Verify Vite proxy configuration in `vite.config.js`

### WebSocket Connection Fails

**Problem:** "WebSocket disconnected" message

**Solution:**
1. Verify backend WebSocket endpoint: `ws://localhost:8000/ws`
2. Check firewall settings
3. Verify proxy configuration supports WebSocket
4. Check browser console for WebSocket errors

### Job Actions Not Working

**Problem:** Pause/Resume/Cancel buttons don't work

**Solution:**
1. Check job status (only certain actions available per status)
2. Verify backend API endpoints are accessible
3. Check browser console for API errors
4. Ensure job_id is valid

### Real-time Updates Not Working

**Problem:** Job status doesn't update automatically

**Solution:**
1. Verify WebSocket connection (check header status indicator)
2. Check browser console for WebSocket errors
3. Verify backend monitoring task is running
4. Check React Query cache configuration

## Security Considerations

### CORS Configuration

Backend CORS is configured for development. For production:

```python
# src/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify production domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Authentication (Future)

To add authentication:

1. **Backend:**
   - Add JWT token generation
   - Require tokens for API endpoints
   - Add token verification middleware

2. **Frontend:**
   - Add login page
   - Store token in localStorage/cookie
   - Add token to API client headers
   - Redirect to login on 401 errors

## Deployment

### Docker Deployment

Create `Dockerfile` for full-stack deployment:

```dockerfile
# Build frontend
FROM node:18 AS frontend
WORKDIR /app/dashboard
COPY dashboard/package*.json ./
RUN npm install
COPY dashboard/ ./
RUN npm run build

# Backend with frontend
FROM python:3.11
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY src/ ./src/
COPY --from=frontend /app/dashboard/dist ./dashboard/dist

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

Production environment variables:

```bash
# Backend
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
MONGODB_URL=mongodb://host:27017/

# Frontend (build time)
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com/ws
```

## Future Enhancements

### Planned Features

1. **User Authentication**
   - Multi-user support
   - Role-based access control
   - User preferences

2. **Advanced Analytics**
   - Custom date ranges
   - Export reports (CSV, PDF)
   - Performance metrics
   - Cost tracking

3. **Recurring Schedule UI**
   - Visual schedule editor
   - Drag-and-drop calendar
   - Bulk operations

4. **Video Preview**
   - Thumbnail generation
   - Video player integration
   - Preview before upload

5. **Notification System**
   - Email notifications
   - Slack integration
   - Custom webhooks

6. **Mobile Responsiveness**
   - Touch-optimized controls
   - Mobile navigation
   - PWA support

## Conclusion

The DOPPELGANGER STUDIO Web Dashboard provides a complete, real-time interface for managing the entire video automation pipeline. With its intuitive design, comprehensive features, and robust architecture, it serves as the perfect control center for automated content creation.

---

**Version:** 1.0.0  
**Last Updated:** January 2025  
**Maintainer:** DOPPELGANGER STUDIO Team
