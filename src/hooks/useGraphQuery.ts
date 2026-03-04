import { useState, useCallback, useRef } from 'react';

export interface QueryResult {
  answer: string;
  query: string;
  session_id: string;
  timestamp: number;
  error: boolean;
}

export interface GraphQueryState {
  results: QueryResult[];
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;
  sendQuery: (query: string) => Promise<void>;
  clearResults: () => void;
}

/**
 * Hook for natural language querying of the OSINT knowledge graph.
 * Manages session state, loading indicators, and result history.
 */
export function useGraphQuery(): GraphQueryState {
  const [results, setResults] = useState<QueryResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sessionIdRef = useRef<string | null>(null);
  const initCheckedRef = useRef(false);

  const checkStatus = useCallback(async () => {
    if (initCheckedRef.current) return;
    initCheckedRef.current = true;
    try {
      const res = await fetch('/api/query/status');
      if (res.ok) {
        const data = await res.json();
        setIsInitialized(data.initialized ?? false);
      }
    } catch {
      setIsInitialized(false);
    }
  }, []);

  const sendQuery = useCallback(async (query: string) => {
    await checkStatus();
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          session_id: sessionIdRef.current,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: QueryResult = await res.json();

      if (data.session_id) {
        sessionIdRef.current = data.session_id;
      }

      setResults((prev) => [...prev, data].slice(-20));
      if (!data.error) setIsInitialized(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Query failed';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [checkStatus]);

  const clearResults = useCallback(() => {
    setResults([]);
    sessionIdRef.current = null;
  }, []);

  return { results, isLoading, isInitialized, error, sendQuery, clearResults };
}
