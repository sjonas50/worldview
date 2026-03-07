import { useState, useEffect, useRef } from 'react';
import type { IntelFeedItem } from '../components/ui/IntelFeed';

/**
 * Military aircraft from Airplanes.live — unfiltered ADS-B data.
 * Unlike FlightRadar24 or adsb.fi, Airplanes.live does not censor
 * LADD-blocked or military-tagged aircraft.
 */
export interface MilFlight {
  hex: string;              // Mode S hex (ICAO24)
  callsign: string;
  registration: string;
  aircraftType: string;     // e.g. "C17A", "KC135R"
  description: string;      // e.g. "C-17A Globemaster III"
  operator: string;         // e.g. "United States Air Force"
  latitude: number;
  longitude: number;
  altitude: number;         // metres (converted from baro ft)
  altitudeFeet: number;     // barometric altitude in feet
  heading: number | null;
  velocity: number | null;  // m/s
  velocityKnots: number | null;
  squawk: string;
  verticalRate: number | null;
  dbFlags: number;          // Airplanes.live database flags (1=mil, 2=interesting, 4=PIA, 8=LADD)
  isMilitary: boolean;
  isLADD: boolean;          // Limiting Aircraft Data Displayed (hidden on FlightRadar24)
  emergency: boolean;
}

const POLL_INTERVAL = 10_000;        // 10s — more frequent for mil tracking
const ERROR_BACKOFF_BASE = 30_000;
const MAX_BACKOFF = 120_000;

/**
 * Fetches global military aircraft from Airplanes.live via backend proxy.
 * This is the only major free, unfiltered military flight data source.
 */
export function useMilFlights(enabled: boolean) {
  const [milFlights, setMilFlights] = useState<MilFlight[]>([]);
  const [feedItems, setFeedItems] = useState<IntelFeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const prevCountRef = useRef(0);
  const consecutiveErrorsRef = useRef(0);

  useEffect(() => {
    if (!enabled) {
      setMilFlights([]);
      setIsLoading(false);
      return;
    }

    let timeoutId: ReturnType<typeof setTimeout>;
    let cancelled = false;

    const fetchData = async () => {
      if (cancelled) return;

      if (milFlights.length === 0 && consecutiveErrorsRef.current === 0) {
        setIsLoading(true);
      }

      try {
        const res = await fetch('/api/flights/military');
        if (!res.ok) throw new Error(`Mil flights proxy HTTP ${res.status}`);
        const data: MilFlight[] = await res.json();

        consecutiveErrorsRef.current = 0;
        setIsLoading(false);
        setMilFlights(data);

        // Intel feed
        if (data.length > 0 && Math.abs(data.length - prevCountRef.current) > 20) {
          prevCountRef.current = data.length;
          const laddCount = data.filter((f) => f.isLADD).length;
          const items: IntelFeedItem[] = [{
            id: `mil-${Date.now()}`,
            time: new Date().toISOString().slice(11, 19),
            type: 'milflight',
            message: `${data.length} military aircraft tracked${laddCount > 0 ? ` (${laddCount} LADD)` : ''}`,
            priority: 'info' as const,
          }];

          // Flag emergency squawks
          const emergencies = data.filter((f) => f.emergency);
          if (emergencies.length > 0) {
            items.push({
              id: `mil-emerg-${Date.now()}`,
              time: new Date().toISOString().slice(11, 19),
              type: 'milflight',
              message: `⚠ ${emergencies.length} military emergency squawk(s)`,
              latitude: emergencies[0].latitude,
              longitude: emergencies[0].longitude,
              priority: 'critical' as const,
            });
          }

          setFeedItems(items);
        }

        console.info(`[MIL] ${data.length} military aircraft from Airplanes.live`);
      } catch (err) {
        consecutiveErrorsRef.current++;
        setIsLoading(false);
        console.error('[MIL] Fetch error:', err);
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

  return { milFlights, feedItems, isLoading };
}
