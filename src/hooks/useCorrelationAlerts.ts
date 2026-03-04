import { useState, useEffect, useRef } from 'react';
import type { IntelFeedItem } from '../components/ui/IntelFeed';

const POLL_INTERVAL = 30_000;       // 30 seconds
const ERROR_BACKOFF_BASE = 30_000;
const MAX_BACKOFF = 120_000;

/**
 * Polls the ingestion service for cross-layer correlation alerts
 * and converts them into IntelFeed items.
 */
export function useCorrelationAlerts(enabled: boolean) {
  const [feedItems, setFeedItems] = useState<IntelFeedItem[]>([]);

  const lastSeenRef = useRef(0);
  const consecutiveErrorsRef = useRef(0);

  useEffect(() => {
    if (!enabled) {
      setFeedItems([]);
      return;
    }

    let timeoutId: ReturnType<typeof setTimeout>;
    let cancelled = false;

    const fetchData = async () => {
      if (cancelled) return;

      try {
        const res = await fetch(`/api/correlations?since=${lastSeenRef.current}&limit=20`);
        if (!res.ok) throw new Error(`Correlations HTTP ${res.status}`);
        const data = await res.json();

        consecutiveErrorsRef.current = 0;

        const alerts = data.alerts || [];
        if (alerts.length > 0) {
          // Update high-water mark
          const maxTs = Math.max(...alerts.map((a: any) => a.detectedAt || 0));
          if (maxTs > lastSeenRef.current) {
            lastSeenRef.current = maxTs;
          }

          const newItems: IntelFeedItem[] = alerts.map((a: any) => ({
            id: `corr-${a.id}`,
            time: new Date(a.detectedAt).toISOString().slice(11, 19),
            type: 'correlation' as const,
            message: `[${(a.confidence || '').toUpperCase()}] ${a.summary || 'Correlation detected'}`,
          }));

          setFeedItems((prev) => [...prev, ...newItems].slice(-10));
        }
      } catch (err) {
        consecutiveErrorsRef.current++;
        console.error('[CORRELATIONS] Fetch error:', err);
      }

      if (cancelled) return;

      const backoff = consecutiveErrorsRef.current > 0
        ? Math.min(ERROR_BACKOFF_BASE * Math.pow(2, consecutiveErrorsRef.current - 1), MAX_BACKOFF)
        : POLL_INTERVAL;

      timeoutId = setTimeout(fetchData, backoff);
    };

    // Initial delay to let ingestion service accumulate data
    timeoutId = setTimeout(fetchData, 10_000);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [enabled]);

  return { feedItems };
}
