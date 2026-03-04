import { useState, useEffect, useRef } from 'react';
import type { IntelFeedItem } from '../components/ui/IntelFeed';

/**
 * A geolocated conflict/news event from GDELT.
 * GDELT monitors global news in 65 languages, updated every 15 minutes.
 */
export interface ConflictEvent {
  id: string;
  name: string;
  url: string;
  latitude: number;
  longitude: number;
  tone: number;             // Sentiment score (negative = hostile)
  goldstein: number;        // Goldstein scale (-10 conflict to +10 cooperation)
  domain: string;           // Source domain
  sourceCountry: string;
  timestamp: string;
  eventType: ConflictEventType;
  shareImage: string;       // Thumbnail URL from article
}

export type ConflictEventType =
  | 'conflict'      // Goldstein < -5
  | 'tension'       // Goldstein -5 to -2
  | 'diplomatic'    // Goldstein -2 to +2
  | 'cooperation'   // Goldstein > +2
  | 'unknown';

function classifyEvent(goldstein: number): ConflictEventType {
  if (goldstein <= -5) return 'conflict';
  if (goldstein <= -2) return 'tension';
  if (goldstein <= 2) return 'diplomatic';
  if (goldstein > 2) return 'cooperation';
  return 'unknown';
}

const POLL_INTERVAL = 900_000;       // 15 minutes (GDELT update cycle)
const ERROR_BACKOFF_BASE = 60_000;
const MAX_BACKOFF = 300_000;

/**
 * Fetches geolocated conflict events from GDELT via backend proxy.
 * No API key required. Returns events from the last 24 hours.
 */
export function useConflictEvents(enabled: boolean) {
  const [events, setEvents] = useState<ConflictEvent[]>([]);
  const [feedItems, setFeedItems] = useState<IntelFeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const prevCountRef = useRef(0);
  const consecutiveErrorsRef = useRef(0);

  useEffect(() => {
    if (!enabled) {
      setEvents([]);
      setIsLoading(false);
      return;
    }

    let timeoutId: ReturnType<typeof setTimeout>;
    let cancelled = false;

    const fetchData = async () => {
      if (cancelled) return;

      if (events.length === 0 && consecutiveErrorsRef.current === 0) {
        setIsLoading(true);
      }

      try {
        const res = await fetch('/api/gdelt');
        if (!res.ok) throw new Error(`GDELT proxy HTTP ${res.status}`);
        const data = await res.json();

        consecutiveErrorsRef.current = 0;
        setIsLoading(false);

        // Parse GDELT GeoJSON features into ConflictEvent[]
        const parsed: ConflictEvent[] = (data.features || []).map((f: any, idx: number) => {
          const props = f.properties || {};
          const goldstein = props.goldstein || 0;
          return {
            id: `gdelt-${props.url || idx}-${Date.now()}`,
            name: props.name || 'Unknown Event',
            url: props.url || '',
            latitude: f.geometry?.coordinates?.[1] || 0,
            longitude: f.geometry?.coordinates?.[0] || 0,
            tone: props.tone || 0,
            goldstein,
            domain: props.domain || '',
            sourceCountry: props.sourcecountry || '',
            timestamp: props.dateadded || new Date().toISOString(),
            eventType: classifyEvent(goldstein),
            shareImage: props.shareimage || '',
          };
        }).filter((e: ConflictEvent) => e.latitude !== 0 && e.longitude !== 0);

        setEvents(parsed);

        // Intel feed
        const conflictCount = parsed.filter((e) => e.eventType === 'conflict').length;
        if (parsed.length > 0 && Math.abs(parsed.length - prevCountRef.current) > 5) {
          prevCountRef.current = parsed.length;
          setFeedItems([{
            id: `gdelt-${Date.now()}`,
            time: new Date().toISOString().slice(11, 19),
            type: 'conflict',
            message: `${parsed.length} geolocated events (${conflictCount} conflict-flagged)`,
          }]);
        }

        console.info(`[GDELT] ${parsed.length} events (${conflictCount} conflicts)`);
      } catch (err) {
        consecutiveErrorsRef.current++;
        setIsLoading(false);
        console.error('[GDELT] Fetch error:', err);
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

  return { events, feedItems, isLoading };
}
