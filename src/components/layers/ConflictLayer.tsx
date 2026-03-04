import { useEffect, useRef } from 'react';
import { useCesium } from 'resium';
import {
  Cartesian3,
  Color,
  NearFarScalar,
  PointPrimitiveCollection,
} from 'cesium';
import type { ConflictEvent, ConflictEventType } from '../../hooks/useConflictEvents';

interface ConflictLayerProps {
  events: ConflictEvent[];
  visible: boolean;
  isTracking?: boolean;
}

/** Color map for conflict event types */
const EVENT_COLORS: Record<ConflictEventType, string> = {
  conflict: '#FF1744',     // Red — active conflict
  tension: '#FF9100',      // Orange — escalation/tension
  diplomatic: '#FFD600',   // Yellow — diplomatic activity
  cooperation: '#00E676',  // Green — cooperation/de-escalation
  unknown: '#90A4AE',      // Gray — unclassified
};

/**
 * Conflict Events Layer (GDELT)
 *
 * Renders geolocated news/conflict events as colored point primitives.
 * Color indicates severity on the Goldstein scale:
 *   Red = active conflict, Orange = tension, Yellow = diplomatic, Green = cooperation.
 * Point size scales with absolute Goldstein value (bigger = more intense).
 *
 * Uses imperative PointPrimitiveCollection for performance.
 */
export default function ConflictLayer({ events, visible, isTracking }: ConflictLayerProps) {
  const { viewer } = useCesium();
  const pointsRef = useRef<PointPrimitiveCollection | null>(null);

  // Create/destroy primitive collection
  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return;

    const points = new PointPrimitiveCollection();
    viewer.scene.primitives.add(points);
    pointsRef.current = points;

    return () => {
      if (!viewer.isDestroyed()) {
        viewer.scene.primitives.remove(points);
      }
      pointsRef.current = null;
    };
  }, [viewer]);

  // Update points when data or visibility changes
  useEffect(() => {
    const points = pointsRef.current;
    if (!points) return;

    points.removeAll();

    if (!visible || events.length === 0) {
      points.show = false;
      return;
    }

    points.show = true;

    for (const event of events) {
      const colorHex = EVENT_COLORS[event.eventType] || EVENT_COLORS.unknown;

      // Size scales with intensity (absolute Goldstein value)
      const intensity = Math.abs(event.goldstein);
      const pixelSize = Math.min(4 + intensity * 0.8, 14);

      // Alpha scales with tone negativity (more negative = more opaque)
      const alpha = event.eventType === 'conflict'
        ? 0.9
        : event.eventType === 'tension'
          ? 0.75
          : 0.55;

      const color = Color.fromCssColorString(colorHex).withAlpha(alpha);

      const position = Cartesian3.fromDegrees(
        event.longitude,
        event.latitude,
        300, // Slight elevation
      );

      points.add({
        position,
        pixelSize,
        color,
        outlineColor: Color.fromCssColorString(colorHex).withAlpha(0.3),
        outlineWidth: event.eventType === 'conflict' ? 2 : 1,
        scaleByDistance: new NearFarScalar(1e3, 1.5, 1e7, 0.3),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      });
    }

    console.log(`[CONFLICT-LAYER] Rendered ${events.length} events`);
  }, [events, visible, isTracking]);

  return null; // Imperative rendering
}
