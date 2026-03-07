import { useState, useMemo } from 'react';
import MobileModal from './MobileModal';

interface IntelFeedItem {
  id: string;
  time: string;
  type: 'flight' | 'seismic' | 'satellite' | 'system' | 'cctv' | 'ship' | 'firms' | 'milflight' | 'conflict' | 'correlation' | 'query';
  message: string;
  latitude?: number;
  longitude?: number;
  priority?: 'critical' | 'high' | 'info';
}

const TYPE_STYLES: Record<string, string> = {
  flight: 'text-wv-cyan',
  seismic: 'text-wv-amber',
  satellite: 'text-wv-green',
  system: 'text-wv-muted',
  cctv: 'text-wv-red',
  ship: 'text-wv-cyan',
  firms: 'text-[#FF6D00]',
  milflight: 'text-[#F44336]',
  conflict: 'text-[#FFD600]',
  correlation: 'text-[#E040FB]',
  query: 'text-[#00E5FF]',
};

const TYPE_BORDERS: Record<string, string> = {
  flight: 'border-wv-cyan/40',
  seismic: 'border-wv-amber/40',
  satellite: 'border-wv-green/40',
  system: 'border-wv-muted/20',
  cctv: 'border-wv-red/40',
  ship: 'border-wv-cyan/40',
  firms: 'border-[#FF6D00]/40',
  milflight: 'border-[#F44336]/40',
  conflict: 'border-[#FFD600]/40',
  correlation: 'border-[#E040FB]/40',
  query: 'border-[#00E5FF]/40',
};

const TYPE_LABELS: Record<string, string> = {
  flight: 'ACFT',
  seismic: 'SEIS',
  satellite: 'SATS',
  system: 'SYS ',
  cctv: 'CCTV',
  ship: 'AIS ',
  firms: 'FIRE',
  milflight: 'MIL ',
  conflict: 'GDLT',
  correlation: 'CORR',
  query: 'QRRY',
};

const FILTER_TABS: { label: string; types: string[] | null }[] = [
  { label: 'ALL', types: null },
  { label: 'ACFT', types: ['flight'] },
  { label: 'MIL', types: ['milflight'] },
  { label: 'SEIS', types: ['seismic'] },
  { label: 'FIRE', types: ['firms'] },
  { label: 'GDLT', types: ['conflict'] },
  { label: 'AIS', types: ['ship'] },
  { label: 'SYS', types: ['system', 'satellite', 'cctv', 'correlation', 'query'] },
];

const PRIORITY_ORDER: Record<string, number> = { critical: 0, high: 1, info: 2 };

interface IntelFeedProps {
  items: IntelFeedItem[];
  isMobile?: boolean;
  onFlyToItem?: (item: IntelFeedItem) => void;
}

export default function IntelFeed({ items, isMobile = false, onFlyToItem }: IntelFeedProps) {
  const [visible, setVisible] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [filter, setFilter] = useState<string>('ALL');

  // Bootstrap message on mount
  const [bootMessages] = useState<IntelFeedItem[]>([
    { id: 'boot-1', time: new Date().toISOString().slice(11, 19), type: 'system', message: 'WORLDVIEW v1.0.0 INITIALISING...' },
    { id: 'boot-2', time: new Date().toISOString().slice(11, 19), type: 'system', message: 'CESIUM 3D ENGINE LOADED' },
    { id: 'boot-3', time: new Date().toISOString().slice(11, 19), type: 'system', message: 'GOOGLE 3D TILES CONNECTED' },
    { id: 'boot-4', time: new Date().toISOString().slice(11, 19), type: 'system', message: 'TACTICAL DISPLAY ONLINE' },
  ]);

  const allItems = useMemo(() => [...bootMessages, ...items].slice(-30), [bootMessages, items]);

  // Filter by selected tab
  const activeTab = FILTER_TABS.find((t) => t.label === filter);
  const filtered = useMemo(() => {
    if (!activeTab?.types) return allItems;
    return allItems.filter((i) => activeTab.types!.includes(i.type));
  }, [allItems, activeTab]);

  // Sort: critical pinned to top, then high, then info/undefined
  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const pa = PRIORITY_ORDER[a.priority ?? 'info'] ?? 2;
      const pb = PRIORITY_ORDER[b.priority ?? 'info'] ?? 2;
      return pa - pb;
    });
  }, [filtered]);

  // Count non-system items as "unread" for the mobile badge
  const liveCount = items.filter((i) => i.type !== 'system').length;

  // Tab counts
  const tabCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const tab of FILTER_TABS) {
      if (!tab.types) {
        counts[tab.label] = allItems.length;
      } else {
        counts[tab.label] = allItems.filter((i) => tab.types!.includes(i.type)).length;
      }
    }
    return counts;
  }, [allItems]);

  const handleItemClick = (item: IntelFeedItem) => {
    if (item.latitude && item.longitude && onFlyToItem) {
      onFlyToItem(item);
    }
  };

  const filterBar = (
    <div className="px-2 py-1.5 border-b border-wv-border shrink-0">
      <div className="flex gap-0.5 flex-wrap">
        {FILTER_TABS.map((tab) => {
          const count = tabCounts[tab.label] || 0;
          const isActive = filter === tab.label;
          return (
            <button
              key={tab.label}
              onClick={() => setFilter(tab.label)}
              className={`px-1.5 py-0.5 rounded text-[7px] tracking-wider transition-all duration-200
                ${isActive
                  ? 'text-wv-cyan bg-white/10 ring-1 ring-wv-cyan/40'
                  : 'text-wv-muted hover:text-wv-text hover:bg-white/5'
                }`}
            >
              {tab.label}
              {count > 0 && <span className="ml-0.5 opacity-60">{count}</span>}
            </button>
          );
        })}
      </div>
    </div>
  );

  const feedList = (
    <div className={isMobile ? 'p-3' : 'max-h-64 overflow-y-auto p-2'}>
      {sorted.length === 0 && (
        <div className="text-center py-4 text-wv-muted text-[9px] tracking-wider">NO EVENTS</div>
      )}
      {sorted.map((item) => {
        const hasLocation = !!(item.latitude && item.longitude);
        return (
          <div
            key={item.id}
            onClick={() => handleItemClick(item)}
            className={`flex items-start gap-1.5 py-0.5 text-[9px] leading-tight border-l-2 pl-2 animate-slide-in
              ${TYPE_BORDERS[item.type] || 'border-wv-muted/20'}
              ${hasLocation ? 'cursor-pointer hover:bg-white/5' : ''}
              ${isMobile ? 'py-1.5 text-[11px]' : ''}`}
          >
            <span className="text-wv-muted shrink-0">{item.time}</span>
            <span className={`shrink-0 font-bold ${TYPE_STYLES[item.type]}`}>
              [{TYPE_LABELS[item.type]}]
            </span>
            {item.priority === 'critical' && (
              <span className="shrink-0 text-[7px] px-1 py-0.5 rounded bg-wv-red/20 text-wv-red font-bold tracking-wider animate-pulse">
                CRIT
              </span>
            )}
            {item.priority === 'high' && (
              <span className="shrink-0 text-[7px] px-1 py-0.5 rounded bg-wv-amber/20 text-wv-amber font-bold tracking-wider">
                HIGH
              </span>
            )}
            <span className="text-wv-text/80 min-w-0">
              {item.message}
              {hasLocation && <span className="ml-1 text-wv-cyan/50 text-[8px]">⟁</span>}
            </span>
          </div>
        );
      })}
    </div>
  );

  /* ── Mobile: badge button + full-screen modal ── */
  if (isMobile) {
    return (
      <>
        <button
          onClick={() => setMobileOpen(true)}
          className="fixed top-3 right-3 z-40 w-11 h-11 rounded-lg panel-glass
                     flex items-center justify-center
                     text-wv-cyan hover:bg-white/10 transition-colors
                     select-none active:scale-95"
          aria-label="Open intel feed"
        >
          <span className="text-lg">📡</span>
          {liveCount > 0 && (
            <span className="absolute -top-1 -right-1 min-w-[16px] h-4 rounded-full bg-wv-cyan
                             text-[8px] text-wv-black font-bold flex items-center justify-center px-0.5">
              {liveCount > 99 ? '99+' : liveCount}
            </span>
          )}
        </button>
        <MobileModal
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          title="Intel Feed"
          icon="📡"
          accent="bg-wv-cyan"
        >
          {filterBar}
          {feedList}
        </MobileModal>
      </>
    );
  }

  /* ── Desktop: fixed side panel ── */
  return (
    <div className="fixed top-4 right-4 w-72 panel-glass panel-tactical rounded-lg overflow-hidden z-40 select-none">
      {/* Header */}
      <div
        className="px-3 py-2 border-b border-wv-border flex items-center justify-between cursor-pointer header-line"
        onClick={() => setVisible(!visible)}
      >
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-wv-cyan animate-pulse" />
          <span className="text-[10px] text-wv-gold/80 tracking-[0.2em] uppercase glow-gold">Intel Feed</span>
        </div>
        <span className="text-[10px] text-wv-muted">{visible ? '▼' : '▶'}</span>
      </div>
      {visible && (
        <>
          {filterBar}
          {feedList}
        </>
      )}
    </div>
  );
}

export type { IntelFeedItem };
