import { useState, useCallback, useRef, useEffect } from 'react';
import type { GraphQueryState } from '../../hooks/useGraphQuery';

interface QueryPanelProps {
  queryState: GraphQueryState;
  isMobile: boolean;
}

export default function QueryPanel({ queryState, isMobile }: QueryPanelProps) {
  const [input, setInput] = useState('');
  const [expanded, setExpanded] = useState(true);
  const resultsEndRef = useRef<HTMLDivElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || queryState.isLoading) return;
    queryState.sendQuery(trimmed);
    setInput('');
  }, [input, queryState]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  // Auto-scroll to latest result
  useEffect(() => {
    resultsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [queryState.results.length]);

  return (
    <div className="border-b border-wv-border">
      {/* Section Header */}
      <div
        className="px-3 py-2 flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${
            queryState.isInitialized ? 'bg-wv-green' : 'bg-wv-amber animate-pulse'
          }`} />
          <span className="text-[9px] text-wv-muted tracking-widest uppercase">
            Graph Query
          </span>
        </div>
        <span className="text-[10px] text-wv-muted">{expanded ? '\u25BC' : '\u25B6'}</span>
      </div>

      {expanded && (
        <div className="px-3 pb-3">
          {/* Input */}
          <div className="flex gap-1 mb-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                queryState.isInitialized
                  ? 'Ask about the knowledge graph...'
                  : 'GraphRAG initializing...'
              }
              disabled={queryState.isLoading}
              className={`
                flex-1 bg-wv-black/50 border border-wv-border rounded px-2 py-1.5
                text-[10px] text-wv-text placeholder-wv-muted/50
                focus:outline-none focus:border-wv-cyan/50
                disabled:opacity-40 disabled:cursor-not-allowed
                ${isMobile ? 'text-[12px] min-h-[40px]' : ''}
              `}
            />
            <button
              onClick={handleSubmit}
              disabled={queryState.isLoading || !input.trim()}
              className={`
                px-2 py-1.5 rounded text-[10px] font-bold tracking-wider
                transition-all duration-200
                ${isMobile ? 'min-h-[40px] px-3' : ''}
                ${queryState.isLoading
                  ? 'text-wv-cyan/50 bg-wv-cyan/5 cursor-wait animate-pulse'
                  : 'text-wv-cyan bg-wv-cyan/10 hover:bg-wv-cyan/20'
                }
                disabled:opacity-30
              `}
            >
              {queryState.isLoading ? '...' : '>'}
            </button>
          </div>

          {/* Results */}
          {queryState.results.length > 0 && (
            <div className="max-h-40 overflow-y-auto space-y-2">
              {queryState.results.map((r, i) => (
                <div key={i} className="text-[9px] leading-tight border-l-2 border-wv-cyan/30 pl-2">
                  <div className="text-wv-cyan/70 mb-0.5">Q: {r.query}</div>
                  <div className={`text-wv-text/80 ${r.error ? 'text-wv-red' : ''}`}>
                    {r.answer}
                  </div>
                </div>
              ))}
              <div ref={resultsEndRef} />
            </div>
          )}

          {/* Error */}
          {queryState.error && (
            <div className="text-[9px] text-wv-red mt-1">{queryState.error}</div>
          )}

          {/* Clear button */}
          {queryState.results.length > 0 && (
            <button
              onClick={queryState.clearResults}
              className="mt-1.5 text-[8px] text-wv-muted/50 hover:text-wv-muted tracking-wider uppercase"
            >
              Clear History
            </button>
          )}
        </div>
      )}
    </div>
  );
}
