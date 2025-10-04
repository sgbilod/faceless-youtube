import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from '../api/jobs'
import toast from 'react-hot-toast'

export function useJobs(status = null) {
  return useQuery({
    queryKey: ['jobs', status],
    queryFn: () => jobsApi.getJobs(status),
  })
}

export function useJob(jobId) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJob(jobId),
    enabled: !!jobId,
  })
}

export function useScheduleJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: jobsApi.scheduleJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      toast.success('Job scheduled successfully')
    },
  })
}

export function useCancelJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: jobsApi.cancelJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      toast.success('Job cancelled')
    },
  })
}

export function usePauseJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: jobsApi.pauseJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      toast.success('Job paused')
    },
  })
}

export function useResumeJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: jobsApi.resumeJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      toast.success('Job resumed')
    },
  })
}
