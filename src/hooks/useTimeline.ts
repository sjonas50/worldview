import { useState, useEffect, useRef, useCallback } from 'react';

export interface TimelineEvent {
  type: 'correlation' | 'thermal' | 'conflict';
  id: string;
  summary: string;
  timestamp: number;
  detail: string;
}

export interface TrajectoryPoint {
  lat: number;
  lon: number;
  alt: number;
  heading: number | null;
  speed: number | null;
  timestamp: number;
  location: string;
}

const POLL_INTERVAL = 60_000; // 1 minute
const ERROR_BACKOFF_BASE = 60_000;
const MAX_BACKOFF = 300_000;

export function useTimeline(enabled: boolean) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const consecutiveErrorsRef = useRef(0);

  useEffect(() => {
    if (!enabled) {
      setEvents([]);
      return;
    }

    let timeoutId: ReturnType<typeof setTimeout>;
    let cancelled = false;

    const fetchEvents = async () => {
      if (cancelled) return;
      if (events.length === 0) setIsLoading(true);

      try {
        const since = Date.now() - 86_400_000; // Last 24h
        const res = await fetch(`/api/timeline?since=${since}&limit=200`);
        if (!res.ok) throw new Error(`Timeline HTTP ${res.status}`);
        const data = await res.json();
        consecutiveErrorsRef.current = 0;
        setIsLoading(false);
        setEvents(data.events || []);
      } catch (err) {
        consecutiveErrorsRef.current++;
        setIsLoading(false);
        console.error('[TIMELINE] Fetch error:', err);
      }

      if (cancelled) return;
      const backoff = consecutiveErrorsRef.current > 0
        ? Math.min(ERROR_BACKOFF_BASE * Math.pow(2, consecutiveErrorsRef.current - 1), MAX_BACKOFF)
        : POLL_INTERVAL;
      timeoutId = setTimeout(fetchEvents, backoff);
    };

    // Initial delay to let ingestion accumulate data
    timeoutId = setTimeout(fetchEvents, 5_000);
    return () => { cancelled = true; clearTimeout(timeoutId); };
  }, [enabled]);

  const fetchTrajectory = useCallback(async (
    entityType: 'aircraft' | 'vessel',
    entityId: string,
  ): Promise<TrajectoryPoint[]> => {
    try {
      const since = Date.now() - 86_400_000;
      const res = await fetch(`/api/trajectory/${entityType}/${entityId}?since=${since}`);
      if (!res.ok) return [];
      const data = await res.json();
      return data.points || [];
    } catch {
      return [];
    }
  }, []);

  return { events, isLoading, fetchTrajectory };
}
