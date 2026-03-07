import { useState, useEffect, useRef } from 'react';
import type { IntelFeedItem } from '../components/ui/IntelFeed';

/**
 * A single FIRMS (Fire Information for Resource Management System) hotspot.
 * Data from NASA VIIRS sensor — 375m resolution, ~3hr latency.
 * High-FRP isolated hotspots in conflict zones at night = potential strikes.
 */
export interface FIRMSHotspot {
  latitude: number;
  longitude: number;
  brightness: number;       // brightness temperature (Kelvin)
  frp: number;              // fire radiative power (MW) — key indicator
  confidence: string;       // 'l' | 'n' | 'h' (low/nominal/high)
  acq_date: string;         // YYYY-MM-DD
  acq_time: string;         // HHMM (UTC)
  satellite: string;        // VIIRS sensor source
  daynight: string;         // 'D' | 'N'
  timestamp: number;        // Unix ms (computed from acq_date + acq_time)
}

const POLL_INTERVAL = 300_000;       // 5 minutes
const ERROR_BACKOFF_BASE = 60_000;
const MAX_BACKOFF = 300_000;

/**
 * Fetches NASA FIRMS thermal anomaly data via the backend proxy.
 * Detects active fires and potential military strike signatures.
 */
export function useFIRMS(enabled: boolean) {
  const [hotspots, setHotspots] = useState<FIRMSHotspot[]>([]);
  const [feedItems, setFeedItems] = useState<IntelFeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const prevCountRef = useRef(0);
  const consecutiveErrorsRef = useRef(0);

  useEffect(() => {
    if (!enabled) {
      setHotspots([]);
      setIsLoading(false);
      return;
    }

    let timeoutId: ReturnType<typeof setTimeout>;
    let cancelled = false;

    const fetchData = async () => {
      if (cancelled) return;

      if (hotspots.length === 0 && consecutiveErrorsRef.current === 0) {
        setIsLoading(true);
      }

      try {
        const res = await fetch('/api/firms');
        if (!res.ok) throw new Error(`FIRMS proxy HTTP ${res.status}`);
        const data: FIRMSHotspot[] = await res.json();

        consecutiveErrorsRef.current = 0;
        setIsLoading(false);
        setHotspots(data);

        // Generate intel feed items for high-confidence hotspots
        const highConf = data.filter((h) => h.confidence === 'h');
        if (data.length > 0 && Math.abs(data.length - prevCountRef.current) > 10) {
          prevCountRef.current = data.length;
          // Pick the highest-FRP hotspot for fly-to location
          const topHotspot = [...data].sort((a, b) => b.frp - a.frp)[0];
          const items: IntelFeedItem[] = [{
            id: `firms-${Date.now()}`,
            time: new Date().toISOString().slice(11, 19),
            type: 'firms',
            message: `${data.length} thermal anomalies detected (${highConf.length} high-conf)`,
            latitude: topHotspot?.latitude,
            longitude: topHotspot?.longitude,
            priority: 'info' as const,
          }];

          // Flag any high-FRP nighttime hotspots as potential strike signatures
          const potentialStrikes = data.filter(
            (h) => h.daynight === 'N' && h.frp > 50 && h.confidence === 'h'
          );
          if (potentialStrikes.length > 0) {
            items.push({
              id: `firms-strike-${Date.now()}`,
              time: new Date().toISOString().slice(11, 19),
              type: 'firms',
              message: `⚠ ${potentialStrikes.length} high-FRP nighttime signature(s)`,
              latitude: potentialStrikes[0].latitude,
              longitude: potentialStrikes[0].longitude,
              priority: 'critical' as const,
            });
          }

          setFeedItems(items);
        }

        console.info(`[FIRMS] ${data.length} hotspots (${highConf.length} high-confidence)`);
      } catch (err) {
        consecutiveErrorsRef.current++;
        setIsLoading(false);
        console.error('[FIRMS] Fetch error:', err);
      }

      if (cancelled) return;

      const backoff = consecutiveErrorsRef.current > 0
        ? Math.min(ERROR_BACKOFF_BASE * Math.pow(2, consecutiveErrorsRef.current - 1), MAX_BACKOFF)
        : POLL_INTERVAL;

      timeoutId = setTimeout(fetchData, backoff);
    };

    fetchData();

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [enabled]);

  return { hotspots, feedItems, isLoading };
}
