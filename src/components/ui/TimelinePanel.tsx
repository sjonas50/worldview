import { useState, useMemo } from 'react';
import type { TimelineEvent } from '../../hooks/useTimeline';

interface TimelinePanelProps {
  events: TimelineEvent[];
  isLoading: boolean;
  visible: boolean;
  onToggle: () => void;
  isMobile: boolean;
}

const EVENT_COLORS: Record<string, string> = {
  correlation: 'bg-[#E040FB]',
  thermal: 'bg-[#FF6D00]',
  conflict: 'bg-[#FFD600]',
};

const EVENT_LABELS: Record<string, string> = {
  correlation: 'CORR',
  thermal: 'FIRE',
  conflict: 'GDLT',
};

export default function TimelinePanel({
  events,
  isLoading,
  visible,
  onToggle,
  isMobile,
}: TimelinePanelProps) {
  const [hoveredEvent, setHoveredEvent] = useState<TimelineEvent | null>(null);

  // Time range: last 24 hours
  const timeRange = useMemo(() => {
    const now = Date.now();
    return { start: now - 86_400_000, end: now };
  }, []);

  // Position events on the timeline (0-100%)
  const positionedEvents = useMemo(() => {
    const range = timeRange.end - timeRange.start;
    return events.map((e) => ({
      ...e,
      position: Math.max(0, Math.min(100,
        ((e.timestamp - timeRange.start) / range) * 100
      )),
    }));
  }, [events, timeRange]);

  if (isMobile) return null;

  return (
    <div className="fixed left-0 right-0 z-30 bottom-8">
      {/* Toggle button */}
      <button
        onClick={onToggle}
        className="absolute -top-6 left-1/2 -translate-x-1/2
                   px-3 py-1 panel-glass rounded-t text-[8px] text-wv-muted
                   tracking-widest uppercase hover:text-wv-text transition-colors"
      >
        TIMELINE
        {isLoading && <span className="ml-1 animate-pulse">...</span>}
        {!isLoading && events.length > 0 && (
          <span className="ml-1 text-wv-cyan">{events.length}</span>
        )}
      </button>

      {visible && (
        <div className="panel-glass h-12 mx-4 rounded-t-lg px-4 flex items-center gap-2">
          {/* Time labels */}
          <span className="text-[8px] text-wv-muted shrink-0">-24h</span>

          {/* Timeline bar */}
          <div className="flex-1 h-4 bg-wv-black/50 rounded relative overflow-hidden">
            {/* Hour markers */}
            {Array.from({ length: 24 }, (_, i) => (
              <div
                key={i}
                className="absolute top-0 bottom-0 w-px bg-wv-border/30"
                style={{ left: `${(i / 24) * 100}%` }}
              />
            ))}

            {/* Event dots */}
            {positionedEvents.map((e, i) => (
              <div
                key={`${e.id}-${i}`}
                className={`absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full
                           cursor-pointer hover:scale-150 transition-transform
                           ${EVENT_COLORS[e.type] || 'bg-wv-cyan'}`}
                style={{ left: `${e.position}%` }}
                onMouseEnter={() => setHoveredEvent(e)}
                onMouseLeave={() => setHoveredEvent(null)}
              />
            ))}
          </div>

          {/* Now label */}
          <span className="text-[8px] text-wv-green shrink-0">NOW</span>

          {/* Event count */}
          <span className="text-[9px] text-wv-muted shrink-0 border-l border-wv-border pl-2">
            {events.length} events
          </span>
        </div>
      )}

      {/* Hover tooltip */}
      {hoveredEvent && visible && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2
                        panel-glass rounded px-3 py-2 max-w-xs z-50 pointer-events-none">
          <div className="flex items-center gap-2 mb-1">
            <span className={`w-2 h-2 rounded-full ${EVENT_COLORS[hoveredEvent.type]}`} />
            <span className="text-[9px] text-wv-muted tracking-wider">
              {EVENT_LABELS[hoveredEvent.type]}
            </span>
            <span className="text-[9px] text-wv-cyan">
              {new Date(hoveredEvent.timestamp).toISOString().slice(11, 19)}Z
            </span>
          </div>
          <div className="text-[9px] text-wv-text/80 leading-tight">
            {hoveredEvent.summary}
          </div>
        </div>
      )}
    </div>
  );
}
