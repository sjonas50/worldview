import { useMemo } from 'react';

interface CameraState {
  latitude: number;
  longitude: number;
  altitude: number;
  heading: number;
  pitch: number;
}

interface DataStatus {
  flights: number;
  satellites: number;
  earthquakes: number;
  cctv: number;
  ships: number;
  firms?: number;
  milFlights?: number;
  conflicts?: number;
}

interface CrosshairProps {
  visible?: boolean;
  camera?: CameraState;
  dataStatus?: DataStatus;
}

/* Compact coord format for HUD */
function fmtCoord(value: number, pos: string, neg: string): string {
  const abs = Math.abs(value);
  const deg = Math.floor(abs);
  const min = Math.floor((abs - deg) * 60);
  const sec = ((abs - deg - min / 60) * 3600).toFixed(0);
  return `${deg}°${min}'${sec}"${value >= 0 ? pos : neg}`;
}

function fmtAlt(m: number): string {
  if (m > 100_000) return `${(m / 1000).toFixed(0)}km`;
  if (m > 1000) return `${(m / 1000).toFixed(1)}km`;
  return `${m.toFixed(0)}m`;
}

/* Compass directions with degree positions */
const COMPASS_POINTS = [
  { deg: 0, label: 'N' },
  { deg: 45, label: 'NE' },
  { deg: 90, label: 'E' },
  { deg: 135, label: 'SE' },
  { deg: 180, label: 'S' },
  { deg: 225, label: 'SW' },
  { deg: 270, label: 'W' },
  { deg: 315, label: 'NW' },
];

const HUD_COLOR = '#22D3EE';

export default function Crosshair({ visible = true, camera, dataStatus }: CrosshairProps) {
  if (!visible) return null;

  const heading = camera?.heading ?? 0;
  const lat = camera?.latitude ?? 0;
  const lon = camera?.longitude ?? 0;
  const alt = camera?.altitude ?? 0;

  // Compass tick marks — generate 36 ticks (every 10°)
  const compassTicks = useMemo(() => {
    const ticks: { deg: number; major: boolean }[] = [];
    for (let d = 0; d < 360; d += 10) {
      ticks.push({ deg: d, major: d % 30 === 0 });
    }
    return ticks;
  }, []);

  // Width of compass strip in SVG units — each degree = 3px
  const DEG_SCALE = 3;
  const STRIP_WIDTH = 400; // visible portion
  const STRIP_CENTER = 960; // center of 1920

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      <svg
        viewBox="0 0 1920 1080"
        preserveAspectRatio="xMidYMid meet"
        className="w-full h-full"
        style={{ opacity: 0.35 }}
      >
        <defs>
          <clipPath id="compassClip">
            <rect x={STRIP_CENTER - STRIP_WIDTH / 2} y="20" width={STRIP_WIDTH} height="40" />
          </clipPath>
        </defs>

        {/* ── Centre Reticle ── */}
        {/* Crosshair lines */}
        <line x1="900" y1="540" x2="945" y2="540" stroke={HUD_COLOR} strokeWidth="0.8" />
        <line x1="975" y1="540" x2="1020" y2="540" stroke={HUD_COLOR} strokeWidth="0.8" />
        <line x1="960" y1="480" x2="960" y2="525" stroke={HUD_COLOR} strokeWidth="0.8" />
        <line x1="960" y1="555" x2="960" y2="600" stroke={HUD_COLOR} strokeWidth="0.8" />
        {/* Centre circle */}
        <circle cx="960" cy="540" r="4" fill="none" stroke={HUD_COLOR} strokeWidth="0.8" />
        {/* Range circles */}
        <circle cx="960" cy="540" r="80" fill="none" stroke={HUD_COLOR} strokeWidth="0.3" strokeDasharray="4 8" />
        <circle cx="960" cy="540" r="160" fill="none" stroke={HUD_COLOR} strokeWidth="0.3" strokeDasharray="4 12" />

        {/* ── Corner Viewport Brackets ── */}
        {/* Top-left */}
        <path d="M 60,60 L 60,100" fill="none" stroke={HUD_COLOR} strokeWidth="1" />
        <path d="M 60,60 L 100,60" fill="none" stroke={HUD_COLOR} strokeWidth="1" />
        {/* Top-right */}
        <path d="M 1860,60 L 1860,100" fill="none" stroke={HUD_COLOR} strokeWidth="1" />
        <path d="M 1860,60 L 1820,60" fill="none" stroke={HUD_COLOR} strokeWidth="1" />
        {/* Bottom-left */}
        <path d="M 60,1020 L 60,980" fill="none" stroke={HUD_COLOR} strokeWidth="1" />
        <path d="M 60,1020 L 100,1020" fill="none" stroke={HUD_COLOR} strokeWidth="1" />
        {/* Bottom-right */}
        <path d="M 1860,1020 L 1860,980" fill="none" stroke={HUD_COLOR} strokeWidth="1" />
        <path d="M 1860,1020 L 1820,1020" fill="none" stroke={HUD_COLOR} strokeWidth="1" />

        {/* Small inner brackets at 1/4 viewport */}
        {/* Top-left inner */}
        <path d="M 420,240 L 420,260 M 420,240 L 440,240" fill="none" stroke={HUD_COLOR} strokeWidth="0.5" />
        {/* Top-right inner */}
        <path d="M 1500,240 L 1500,260 M 1500,240 L 1480,240" fill="none" stroke={HUD_COLOR} strokeWidth="0.5" />
        {/* Bottom-left inner */}
        <path d="M 420,840 L 420,820 M 420,840 L 440,840" fill="none" stroke={HUD_COLOR} strokeWidth="0.5" />
        {/* Bottom-right inner */}
        <path d="M 1500,840 L 1500,820 M 1500,840 L 1480,840" fill="none" stroke={HUD_COLOR} strokeWidth="0.5" />

        {/* ── Compass Strip (top centre) ── */}
        <g clipPath="url(#compassClip)">
          {/* Background bar */}
          <rect x={STRIP_CENTER - STRIP_WIDTH / 2} y="20" width={STRIP_WIDTH} height="40"
            fill="rgba(8, 8, 12, 0.4)" />

          {/* Tick marks and labels — translated by heading */}
          <g transform={`translate(${STRIP_CENTER - heading * DEG_SCALE}, 0)`}>
            {/* Render 3 full rotations (-360 to 720) to prevent gaps */}
            {[-360, 0, 360].map((offset) => (
              <g key={offset}>
                {compassTicks.map(({ deg, major }) => {
                  const x = (deg + offset) * DEG_SCALE;
                  return (
                    <line
                      key={`${offset}-${deg}`}
                      x1={x} y1={major ? 38 : 44}
                      x2={x} y2={58}
                      stroke={HUD_COLOR}
                      strokeWidth={major ? 0.8 : 0.4}
                    />
                  );
                })}
                {COMPASS_POINTS.map(({ deg: d, label }) => {
                  const x = (d + offset) * DEG_SCALE;
                  return (
                    <text
                      key={`${offset}-${label}`}
                      x={x} y={34}
                      fill={HUD_COLOR}
                      fontSize="11"
                      fontFamily="monospace"
                      textAnchor="middle"
                      fontWeight={label === 'N' ? 'bold' : 'normal'}
                    >
                      {label}
                    </text>
                  );
                })}
              </g>
            ))}
          </g>

          {/* Centre indicator triangle */}
          <polygon
            points={`${STRIP_CENTER - 4},20 ${STRIP_CENTER + 4},20 ${STRIP_CENTER},27`}
            fill={HUD_COLOR}
          />
        </g>

        {/* Heading readout below compass */}
        <text
          x={STRIP_CENTER} y="75"
          fill={HUD_COLOR}
          fontSize="10"
          fontFamily="monospace"
          textAnchor="middle"
        >
          HDG {heading.toFixed(1)}°
        </text>

        {/* ── Bottom-Left Data Readout ── */}
        <g>
          <text x="80" y="950" fill={HUD_COLOR} fontSize="10" fontFamily="monospace" opacity="0.9">
            LAT {fmtCoord(lat, 'N', 'S')}
          </text>
          <text x="80" y="966" fill={HUD_COLOR} fontSize="10" fontFamily="monospace" opacity="0.9">
            LON {fmtCoord(lon, 'E', 'W')}
          </text>
          <text x="80" y="982" fill={HUD_COLOR} fontSize="10" fontFamily="monospace" opacity="0.9">
            ALT {fmtAlt(alt)}
          </text>
        </g>

        {/* ── Bottom-Right Data Feeds ── */}
        {dataStatus && (
          <g textAnchor="end">
            <text x="1840" y="935" fill={HUD_COLOR} fontSize="9" fontFamily="monospace" opacity="0.7">
              ACFT {dataStatus.flights}
            </text>
            <text x="1840" y="949" fill={HUD_COLOR} fontSize="9" fontFamily="monospace" opacity="0.7">
              SATS {dataStatus.satellites}
            </text>
            <text x="1840" y="963" fill={HUD_COLOR} fontSize="9" fontFamily="monospace" opacity="0.7">
              AIS  {dataStatus.ships}
            </text>
            <text x="1840" y="977" fill={HUD_COLOR} fontSize="9" fontFamily="monospace" opacity="0.7">
              MIL  {dataStatus.milFlights ?? 0}
            </text>
            <text x="1840" y="991" fill={HUD_COLOR} fontSize="9" fontFamily="monospace" opacity="0.7">
              SEIS {dataStatus.earthquakes}
            </text>
          </g>
        )}

        {/* ── Side altitude ladder (left) ── */}
        <line x1="50" y1="340" x2="50" y2="740" stroke={HUD_COLOR} strokeWidth="0.4" />
        {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => {
          const y = 340 + i * 50;
          return (
            <line key={i} x1="45" y1={y} x2="55" y2={y} stroke={HUD_COLOR} strokeWidth="0.5" />
          );
        })}

        {/* ── Side heading ladder (right) ── */}
        <line x1="1870" y1="340" x2="1870" y2="740" stroke={HUD_COLOR} strokeWidth="0.4" />
        {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => {
          const y = 340 + i * 50;
          return (
            <line key={i} x1="1865" y1={y} x2="1875" y2={y} stroke={HUD_COLOR} strokeWidth="0.5" />
          );
        })}
      </svg>
    </div>
  );
}
