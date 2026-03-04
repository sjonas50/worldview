import { useEffect, useRef } from 'react';
import { useCesium } from 'resium';
import {
  Cartesian3,
  Color,
  PolylineCollection,
  Material,
} from 'cesium';
import type { TrajectoryPoint } from '../../hooks/useTimeline';

interface TrajectoryLayerProps {
  points: TrajectoryPoint[];
  visible: boolean;
  color?: string; // CSS hex color
}

/**
 * Renders a trajectory polyline on the globe from historical position data.
 * Uses imperative PolylineCollection for performance.
 */
export default function TrajectoryLayer({ points, visible, color = '#00E5FF' }: TrajectoryLayerProps) {
  const { viewer } = useCesium();
  const polylinesRef = useRef<PolylineCollection | null>(null);

  // Create/destroy polyline collection
  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return;

    const polylines = new PolylineCollection();
    viewer.scene.primitives.add(polylines);
    polylinesRef.current = polylines;

    return () => {
      if (!viewer.isDestroyed()) {
        viewer.scene.primitives.remove(polylines);
      }
      polylinesRef.current = null;
    };
  }, [viewer]);

  // Update polyline when points change
  useEffect(() => {
    const polylines = polylinesRef.current;
    if (!polylines) return;

    polylines.removeAll();

    if (!visible || points.length < 2) {
      polylines.show = false;
      return;
    }

    polylines.show = true;

    const positions = points.map((p) =>
      Cartesian3.fromDegrees(p.lon, p.lat, (p.alt || 0) + 50)
    );

    // Main trail line
    polylines.add({
      positions,
      width: 2.5,
      material: Material.fromType('Color', {
        color: Color.fromCssColorString(color).withAlpha(0.8),
      }),
    });

    // Ground track (projected shadow)
    const groundPositions = points.map((p) =>
      Cartesian3.fromDegrees(p.lon, p.lat, 10)
    );
    polylines.add({
      positions: groundPositions,
      width: 1.5,
      material: Material.fromType('Color', {
        color: Color.fromCssColorString(color).withAlpha(0.2),
      }),
    });
  }, [points, visible, color]);

  return null;
}
