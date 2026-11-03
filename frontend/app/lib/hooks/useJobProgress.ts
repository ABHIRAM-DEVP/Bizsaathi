/**
 * Hook for SSE job progress tracking with Last-Event-ID reconnection.
 */

import { useEffect, useState } from 'react';
import { getBrowserApiUrl } from '../api-url';

export interface JobEvent {
  seq: number;
  node: string;
  event: string;
  timestamp: string;
}

interface UseJobProgressOptions {
  jobId: string;
  onComplete?: (result: unknown) => void;
  onError?: (error: string) => void;
}

export function useJobProgress({ jobId, onComplete, onError }: UseJobProgressOptions) {
  const [events, setEvents] = useState<JobEvent[]>([]);
  const [status, setStatus] = useState<'pending' | 'running' | 'completed' | 'failed' | 'blocked'>('pending');
  const [lastSeq, setLastSeq] = useState(0);

  useEffect(() => {
    if (!jobId) return;

    let url: string;
    try {
      url = getBrowserApiUrl(`/jobs/${jobId}/events`);
    } catch (error) {
      onError?.(error instanceof Error ? error.message : "NEXT_PUBLIC_API_URL is not configured.");
      return;
    }
    const eventUrl = new URL(url);
    if (lastSeq > 0) {
      eventUrl.searchParams.set('after_seq', String(lastSeq));
    }

    const eventSource = new EventSource(eventUrl.toString(), { withCredentials: true });

    eventSource.addEventListener('job_event', (e) => {
      try {
        const event = JSON.parse(e.data) as JobEvent;
        setEvents((prev) => [...prev, event]);
        setLastSeq(event.seq);
      } catch (err) {
        console.error('Failed to parse job event:', err);
      }
    });

    eventSource.addEventListener('job_status', (e) => {
      try {
        const data = JSON.parse(e.data);
        setStatus(data.status);
        
        if (data.status === 'completed' && onComplete) {
          onComplete(data.result_ref);
          eventSource.close();
        } else if ((data.status === 'failed' || data.status === 'blocked') && onError) {
          onError(data.error_code || 'Unknown error');
          eventSource.close();
        }
      } catch (err) {
        console.error('Failed to parse job status:', err);
      }
    });

    eventSource.addEventListener('heartbeat', () => {
      // Keep connection alive
    });

    eventSource.onerror = () => {
      // EventSource automatically reconnects with Last-Event-ID
      console.log('SSE connection error, reconnecting...');
    };

    return () => {
      eventSource.close();
    };
  }, [jobId, lastSeq, onComplete, onError]);

  return { events, status };
}
