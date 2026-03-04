import { useEffect, useRef } from 'react';
import { useCesium } from 'resium';
import {
  WebMapTileServiceImageryProvider,
  WebMercatorTilingScheme,
  type ImageryLayer,
} from 'cesium';

interface GibsImageryLayerProps {
  trueColorVisible: boolean;
  nightLightsVisible: boolean;
}

/** Today's date in YYYY-MM-DD (UTC) for GIBS TIME dimension */
function todayUTC(): string {
  // GIBS tiles for "today" may not be available until ~3-5h after acquisition.
  // Use yesterday to ensure tiles exist.
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - 1);
  return d.toISOString().slice(0, 10);
}

const GIBS_BASE = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best';
const TILE_MATRIX_SET = 'GoogleMapsCompatible_Level9';

function createGibsProvider(layerName: string): WebMapTileServiceImageryProvider {
  return new WebMapTileServiceImageryProvider({
    url: `${GIBS_BASE}/wmts.cgi`,
    layer: layerName,
    style: 'default',
    format: 'image/png',
    tileMatrixSetID: TILE_MATRIX_SET,
    tileMatrixLabels: [
      '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    ],
    tilingScheme: new WebMercatorTilingScheme(),
    maximumLevel: 9,
    dimensions: { TIME: todayUTC() },
  });
}

/**
 * Manages NASA GIBS imagery overlays on the Cesium globe.
 * Two independent layers: VIIRS True Color and VIIRS Day/Night Band.
 */
export default function GibsImageryLayer({ trueColorVisible, nightLightsVisible }: GibsImageryLayerProps) {
  const { viewer } = useCesium();
  const trueColorRef = useRef<ImageryLayer | null>(null);
  const nightLightsRef = useRef<ImageryLayer | null>(null);

  // VIIRS True Color
  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return;

    if (trueColorVisible && !trueColorRef.current) {
      const provider = createGibsProvider('VIIRS_SNPP_CorrectedReflectance_TrueColor');
      const layer = viewer.imageryLayers.addImageryProvider(provider);
      layer.alpha = 1.0;
      trueColorRef.current = layer;
    } else if (!trueColorVisible && trueColorRef.current) {
      viewer.imageryLayers.remove(trueColorRef.current);
      trueColorRef.current = null;
    }

    return () => {
      if (trueColorRef.current && viewer && !viewer.isDestroyed()) {
        try { viewer.imageryLayers.remove(trueColorRef.current); } catch { /* already removed */ }
        trueColorRef.current = null;
      }
    };
  }, [trueColorVisible, viewer]);

  // VIIRS Day/Night Band
  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return;

    if (nightLightsVisible && !nightLightsRef.current) {
      const provider = createGibsProvider('VIIRS_SNPP_DayNightBand_ENCC');
      const layer = viewer.imageryLayers.addImageryProvider(provider);
      layer.alpha = 0.8;
      nightLightsRef.current = layer;
    } else if (!nightLightsVisible && nightLightsRef.current) {
      viewer.imageryLayers.remove(nightLightsRef.current);
      nightLightsRef.current = null;
    }

    return () => {
      if (nightLightsRef.current && viewer && !viewer.isDestroyed()) {
        try { viewer.imageryLayers.remove(nightLightsRef.current); } catch { /* already removed */ }
        nightLightsRef.current = null;
      }
    };
  }, [nightLightsVisible, viewer]);

  return null;
}
