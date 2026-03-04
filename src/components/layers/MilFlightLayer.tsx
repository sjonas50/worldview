import { useEffect, useRef, useCallback } from 'react';
import { useCesium } from 'resium';
import {
  Cartesian3,
  Color,
  NearFarScalar,
  CallbackProperty,
  Math as CesiumMath,
  BillboardCollection,
  PointPrimitiveCollection,
  PolylineCollection,
  VerticalOrigin,
  Cartographic,
} from 'cesium';
import type { MilFlight } from '../../hooks/useMilFlights';

interface MilFlightLayerProps {
  milFlights: MilFlight[];
  visible: boolean;
  isTracking?: boolean;
}

// Dead-reckoning state for smooth 60fps movement between data updates
interface MilFlightState {
  lat: number;
  lon: number;
  alt: number;
  heading: number | null;
  velocity: number | null; // m/s
  lastUpdate: number;
}

/**
 * Military Flight Layer
 *
 * Renders military aircraft from Airplanes.live with distinctive styling:
 * - Red diamonds for confirmed military
 * - Amber for LADD-blocked aircraft (hidden on commercial trackers)
 * - Pulsing outline for emergency squawks
 *
 * Uses dead-reckoning extrapolation for smooth movement (same as FlightLayer).
 */
export default function MilFlightLayer({ milFlights, visible, isTracking }: MilFlightLayerProps) {
  const { viewer } = useCesium();
  const billboardsRef = useRef<BillboardCollection | null>(null);
  const stateMapRef = useRef<Map<string, MilFlightState>>(new Map());
  const dataRef = useRef<MilFlight[]>([]);

  // Keep data ref in sync
  useEffect(() => {
    dataRef.current = milFlights;

    // Update dead-reckoning state
    const now = Date.now();
    const stateMap = stateMapRef.current;
    const activeHexes = new Set<string>();

    for (const f of milFlights) {
      activeHexes.add(f.hex);
      stateMap.set(f.hex, {
        lat: f.latitude,
        lon: f.longitude,
        alt: f.altitude,
        heading: f.heading,
        velocity: f.velocity,
        lastUpdate: now,
      });
    }

    // Prune stale entries
    for (const hex of stateMap.keys()) {
      if (!activeHexes.has(hex)) stateMap.delete(hex);
    }
  }, [milFlights]);

  // Create/destroy billboard collection
  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return;

    const billboards = new BillboardCollection({ scene: viewer.scene });
    viewer.scene.primitives.add(billboards);
    billboardsRef.current = billboards;

    return () => {
      if (!viewer.isDestroyed()) {
        viewer.scene.primitives.remove(billboards);
      }
      billboardsRef.current = null;
    };
  }, [viewer]);

  // Create military aircraft icon (red diamond)
  const createMilIcon = useCallback((isLADD: boolean, emergency: boolean): HTMLCanvasElement => {
    const canvas = document.createElement('canvas');
    const size = 24;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d')!;

    // Diamond shape
    ctx.beginPath();
    ctx.moveTo(size / 2, 2);           // top
    ctx.lineTo(size - 2, size / 2);    // right
    ctx.lineTo(size / 2, size - 2);    // bottom
    ctx.lineTo(2, size / 2);           // left
    ctx.closePath();

    if (emergency) {
      ctx.fillStyle = '#FF1744';
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 2;
    } else if (isLADD) {
      ctx.fillStyle = '#FFB300'; // Amber for LADD
      ctx.strokeStyle = '#FF8F00';
      ctx.lineWidth = 1.5;
    } else {
      ctx.fillStyle = '#F44336'; // Red for military
      ctx.strokeStyle = '#D32F2F';
      ctx.lineWidth = 1;
    }

    ctx.fill();
    ctx.stroke();

    // Centre dot
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, 2, 0, Math.PI * 2);
    ctx.fillStyle = '#FFFFFF';
    ctx.fill();

    return canvas;
  }, []);

  // Update billboards when data or visibility changes
  useEffect(() => {
    const billboards = billboardsRef.current;
    if (!billboards) return;

    billboards.removeAll();

    if (!visible || milFlights.length === 0) {
      billboards.show = false;
      return;
    }

    billboards.show = true;

    // Pre-create icon variants
    const milIcon = createMilIcon(false, false);
    const laddIcon = createMilIcon(true, false);
    const emergIcon = createMilIcon(false, true);

    for (const flight of milFlights) {
      const icon = flight.emergency ? emergIcon
        : flight.isLADD ? laddIcon
        : milIcon;

      const position = Cartesian3.fromDegrees(
        flight.longitude,
        flight.latitude,
        flight.altitude,
      );

      const rotation = flight.heading != null
        ? CesiumMath.toRadians(-flight.heading)
        : 0;

      billboards.add({
        position,
        image: icon,
        rotation,
        verticalOrigin: VerticalOrigin.CENTER,
        scale: 1.0,
        scaleByDistance: new NearFarScalar(5e3, 1.5, 5e6, 0.4),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      });
    }

    console.log(`[MIL-LAYER] Rendered ${milFlights.length} military aircraft`);
  }, [milFlights, visible, isTracking, createMilIcon]);

  // Dead-reckoning: update billboard positions every frame for smooth movement
  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return;

    let lastBulkUpdate = 0;

    const onPreUpdate = () => {
      const billboards = billboardsRef.current;
      if (!billboards || !visible || billboards.length === 0) return;

      const now = Date.now();
      // Bulk-update all aircraft every 1 second (avoid per-frame overhead for all)
      if (now - lastBulkUpdate < 1000) return;
      lastBulkUpdate = now;

      const flights = dataRef.current;
      const stateMap = stateMapRef.current;

      for (let i = 0; i < billboards.length && i < flights.length; i++) {
        const flight = flights[i];
        const state = stateMap.get(flight.hex);
        if (!state) continue;

        const dtSec = (now - state.lastUpdate) / 1000;
        let lat = state.lat;
        let lon = state.lon;

        // Dead-reckon if we have heading + velocity and data is <120s old
        if (
          state.heading != null &&
          state.velocity != null &&
          state.velocity > 10 &&
          dtSec > 0 &&
          dtSec < 120
        ) {
          const headRad = CesiumMath.toRadians(state.heading);
          lat += (Math.cos(headRad) * state.velocity * dtSec) / 111320;
          const cosLat = Math.cos(lat * (Math.PI / 180)) || 0.0001;
          lon += (Math.sin(headRad) * state.velocity * dtSec) / (111320 * cosLat);
        }

        const billboard = billboards.get(i);
        billboard.position = Cartesian3.fromDegrees(lon, lat, state.alt);
      }
    };

    viewer.scene.preUpdate.addEventListener(onPreUpdate);
    return () => {
      if (!viewer.isDestroyed()) {
        viewer.scene.preUpdate.removeEventListener(onPreUpdate);
      }
    };
  }, [viewer, visible]);

  return null; // Imperative rendering
}
