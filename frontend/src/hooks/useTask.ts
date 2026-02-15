import { useQuery } from '@tanstack/react-query';
import { getTask } from '../api/client';
import type { TaskStatus } from '../api/types';

interface UseTaskOptions {
  enabled?: boolean;
}

export function useTask(taskId: string | null, options: UseTaskOptions = {}) {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['task', taskId],
    queryFn: () => getTask(taskId!),
    enabled: enabled && !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Keep polling while pending or in_progress
      if (data && ['pending', 'in_progress'].includes(data.status)) {
        return 1000; // Poll every second
      }
      return false; // Stop polling
    },
    refetchIntervalInBackground: false,
  });
}

export function isTaskRunning(status?: TaskStatus): boolean {
  return status?.status === 'pending' || status?.status === 'in_progress';
}

export function isTaskComplete(status?: TaskStatus): boolean {
  return status?.status === 'completed';
}

export function isTaskFailed(status?: TaskStatus): boolean {
  return status?.status === 'failed';
}
