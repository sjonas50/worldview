import { useEffect, useRef } from 'react';
import { useCesium } from 'resium';
import {
  Cartesian3,
  Color,
  NearFarScalar,
  HeightReference,
  PointPrimitiveCollection,
  BillboardCollection,
  VerticalOrigin,
} from 'cesium';
import type { FIRMSHotspot } from '../../hooks/useFIRMS';

interface FIRMSLayerProps {
  hotspots: FIRMSHotspot[];
  visible: boolean;
  isTracking?: boolean;
}

/**
 * FIRMS Thermal Anomaly Layer
 *
 * Renders NASA FIRMS fire/thermal hotspots as pulsing point primitives
 * on the CesiumJS globe. Point size scales with fire radiative power (FRP).
 * High-confidence nighttime hotspots render in bright red with larger markers.
 *
 * Uses imperative PointPrimitiveCollection for performance (same pattern
 * as FlightLayer and ShipLayer).
 */
export default function FIRMSLayer({ hotspots, visible, isTracking }: FIRMSLayerProps) {
  const { viewer } = useCesium();
  const pointsRef = useRef<PointPrimitiveCollection | null>(null);
  const labelsRef = useRef<BillboardCollection | null>(null);

  // Create/destroy primitive collections
  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return;

    const points = new PointPrimitiveCollection();
    const labels = new BillboardCollection({ scene: viewer.scene });
    viewer.scene.primitives.add(points);
    viewer.scene.primitives.add(labels);
    pointsRef.current = points;
    labelsRef.current = labels;

    return () => {
      if (!viewer.isDestroyed()) {
        viewer.scene.primitives.remove(points);
        viewer.scene.primitives.remove(labels);
      }
      pointsRef.current = null;
      labelsRef.current = null;
    };
  }, [viewer]);

  // Update points when data or visibility changes
  useEffect(() => {
    const points = pointsRef.current;
    const labels = labelsRef.current;
    if (!points || !labels) return;

    points.removeAll();
    labels.removeAll();

    if (!visible || hotspots.length === 0) {
      points.show = false;
      labels.show = false;
      return;
    }

    points.show = true;
    labels.show = true;

    for (const hotspot of hotspots) {
      const isHighConf = hotspot.confidence === 'h';
      const isNight = hotspot.daynight === 'N';
      const isPotentialStrike = isNight && hotspot.frp > 50 && isHighConf;

      // Size: 4px base, scales up with FRP (max ~20px)
      const pixelSize = Math.min(4 + Math.sqrt(hotspot.frp) * 1.5, 20);

      // Color: bright red for high-FRP night, orange for day, dim for low-conf
      let color: Color;
      if (isPotentialStrike) {
        color = Color.fromCssColorString('#FF1744').withAlpha(0.95); // Bright strike red
      } else if (isHighConf) {
        color = Color.fromCssColorString('#FF6D00').withAlpha(0.85); // High-conf orange
      } else if (hotspot.confidence === 'n') {
        color = Color.fromCssColorString('#FF9100').withAlpha(0.65); // Nominal amber
      } else {
        color = Color.fromCssColorString('#FFB74D').withAlpha(0.45); // Low-conf pale
      }

      const outlineColor = isPotentialStrike
        ? Color.fromCssColorString('#FF1744').withAlpha(0.6)
        : Color.fromCssColorString('#FF6D00').withAlpha(0.3);

      const position = Cartesian3.fromDegrees(
        hotspot.longitude,
        hotspot.latitude,
        500, // Slight elevation so points render above terrain
      );

      points.add({
        position,
        pixelSize,
        color,
        outlineColor,
        outlineWidth: isPotentialStrike ? 3 : 1,
        scaleByDistance: new NearFarScalar(1e3, 2.0, 8e6, 0.4),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      });

      // Add a label for high-FRP potential strikes
      if (isPotentialStrike) {
        const canvas = document.createElement('canvas');
        const size = 32;
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          // Pulsing ring effect (static — animation handled by shader)
          ctx.beginPath();
          ctx.arc(size / 2, size / 2, size / 2 - 2, 0, Math.PI * 2);
          ctx.strokeStyle = '#FF1744';
          ctx.lineWidth = 2;
          ctx.stroke();

          // Inner dot
          ctx.beginPath();
          ctx.arc(size / 2, size / 2, 4, 0, Math.PI * 2);
          ctx.fillStyle = '#FF1744';
          ctx.fill();
        }

        labels.add({
          position,
          image: canvas,
          verticalOrigin: VerticalOrigin.CENTER,
          scale: 1.5,
          scaleByDistance: new NearFarScalar(1e3, 2.0, 5e6, 0.5),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        });
      }
    }

    console.log(`[FIRMS-LAYER] Rendered ${hotspots.length} hotspots`);
  }, [hotspots, visible, isTracking]);

  return null; // Imperative rendering — no React DOM output
}
