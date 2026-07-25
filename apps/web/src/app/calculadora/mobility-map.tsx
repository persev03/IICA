'use client';

import type { LayerGroup, Map as LeafletMap, Polyline } from 'leaflet';
import { useEffect, useRef, useState } from 'react';

type Point = {
  lat: number;
  lng: number;
};

type DistanceSource = 'route' | 'approximate';

type MobilityMapProps = {
  center: [number, number];
  cityCode: string;
  onDistanceChange: (
    distanceKilometers: number | null,
    source: DistanceSource | null,
  ) => void;
};

type OsrmResponse = {
  routes?: {
    distance: number;
    geometry: { coordinates: [number, number][] };
  }[];
};

function approximateDistance(points: Point[]) {
  const earthRadiusKm = 6371;
  return points.slice(1).reduce((total, point, index) => {
    const previous = points[index];
    const latitudeDelta = ((point.lat - previous.lat) * Math.PI) / 180;
    const longitudeDelta = ((point.lng - previous.lng) * Math.PI) / 180;
    const startLatitude = (previous.lat * Math.PI) / 180;
    const endLatitude = (point.lat * Math.PI) / 180;
    const haversine =
      Math.sin(latitudeDelta / 2) ** 2 +
      Math.cos(startLatitude) *
        Math.cos(endLatitude) *
        Math.sin(longitudeDelta / 2) ** 2;
    return (
      total +
      earthRadiusKm * 2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine))
    );
  }, 0);
}

export function MobilityMap({
  center,
  cityCode,
  onDistanceChange,
}: MobilityMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const markersRef = useRef<LayerGroup | null>(null);
  const routeRef = useRef<Polyline | null>(null);
  const leafletRef = useRef<typeof import('leaflet') | null>(null);
  const requestRef = useRef<AbortController | null>(null);
  const centerRef = useRef(center);
  const [mapReady, setMapReady] = useState(false);
  const [points, setPoints] = useState<Point[]>([]);
  const [distance, setDistance] = useState<number | null>(null);
  const [status, setStatus] = useState(
    'Haz clic en el mapa para marcar origen, destino y paradas.',
  );

  centerRef.current = center;

  useEffect(() => {
    let active = true;

    async function initializeMap() {
      if (!containerRef.current || mapRef.current) return;
      const L = await import('leaflet');
      if (!active || !containerRef.current) return;

      leafletRef.current = L;
      const map = L.map(containerRef.current, {
        scrollWheelZoom: false,
        zoomControl: true,
      }).setView(centerRef.current, 12);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution:
          '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);
      markersRef.current = L.layerGroup().addTo(map);
      routeRef.current = L.polyline([], {
        color: '#d9ff65',
        opacity: 0.95,
        weight: 5,
      }).addTo(map);
      map.on('click', (event) => {
        setPoints((current) =>
          current.length >= 5
            ? current
            : [...current, { lat: event.latlng.lat, lng: event.latlng.lng }],
        );
      });
      mapRef.current = map;
      setMapReady(true);
    }

    void initializeMap();
    return () => {
      active = false;
      requestRef.current?.abort();
      mapRef.current?.remove();
      mapRef.current = null;
      leafletRef.current = null;
    };
  }, []);

  useEffect(() => {
    setPoints([]);
    setDistance(null);
    setStatus('Haz clic en el mapa para marcar origen, destino y paradas.');
    onDistanceChange(null, null);
    mapRef.current?.setView(center, 12);
  }, [center, cityCode, onDistanceChange]);

  useEffect(() => {
    const L = leafletRef.current;
    const markerLayer = markersRef.current;
    const routeLayer = routeRef.current;
    if (!mapReady || !L || !markerLayer || !routeLayer) return;

    requestRef.current?.abort();
    markerLayer.clearLayers();
    points.forEach((point, index) => {
      L.marker([point.lat, point.lng], {
        icon: L.divIcon({
          className: 'route-marker',
          html: `<span>${index + 1}</span>`,
          iconAnchor: [16, 16],
          iconSize: [32, 32],
        }),
      }).addTo(markerLayer);
    });

    const directLine = points.map(
      (point) => [point.lat, point.lng] as [number, number],
    );
    routeLayer.setLatLngs(directLine);
    if (points.length < 2) {
      setDistance(null);
      onDistanceChange(null, null);
      setStatus(
        points.length
          ? 'Marca al menos un segundo punto para estimar el recorrido.'
          : 'Haz clic en el mapa para marcar origen, destino y paradas.',
      );
      return;
    }

    const controller = new AbortController();
    requestRef.current = controller;
    const coordinates = points.map((point) => `${point.lng},${point.lat}`).join(';');
    setStatus('Calculando la ruta por calles…');

    void fetch(
      `https://router.project-osrm.org/route/v1/driving/${coordinates}?overview=full&geometries=geojson`,
      { signal: controller.signal },
    )
      .then(async (response) => {
        if (!response.ok) throw new Error('route-unavailable');
        const payload = (await response.json()) as OsrmResponse;
        const route = payload.routes?.[0];
        if (!route) throw new Error('route-unavailable');
        routeLayer.setLatLngs(
          route.geometry.coordinates.map(
            ([longitude, latitude]) =>
              [latitude, longitude] as [number, number],
          ),
        );
        const kilometers = route.distance / 1000;
        setDistance(kilometers);
        setStatus('Ruta calculada sobre la red vial de OpenStreetMap.');
        onDistanceChange(kilometers, 'route');
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        const kilometers = approximateDistance(points) * 1.25;
        setDistance(kilometers);
        setStatus('Ruta aproximada localmente; el servicio vial no respondió.');
        onDistanceChange(kilometers, 'approximate');
      });
  }, [mapReady, onDistanceChange, points]);

  return (
    <section className="mobility-map" aria-labelledby="mobility-map-title">
      <div className="map-heading">
        <div>
          <span className="map-kicker">Recorrido habitual</span>
          <h3 id="mobility-map-title">Marca tus puntos en el mapa</h3>
        </div>
        <span className="point-counter">{points.length}/5 puntos</span>
      </div>
      <div
        className="map-canvas"
        ref={containerRef}
        aria-label="Mapa interactivo para marcar el recorrido habitual"
      />
      <div className="map-summary" aria-live="polite">
        <span>{status}</span>
        {distance !== null ? <strong>{distance.toFixed(1)} km por trayecto</strong> : null}
      </div>
      <div className="map-actions">
        <button
          className="map-button"
          type="button"
          disabled={!points.length}
          onClick={() => setPoints((current) => current.slice(0, -1))}
        >
          Deshacer último
        </button>
        <button
          className="map-button"
          type="button"
          disabled={!points.length}
          onClick={() => setPoints([])}
        >
          Limpiar ruta
        </button>
      </div>
      <small>
        Los puntos no se guardan. La ruta se consulta temporalmente con OSRM y los
        mapas usan datos de OpenStreetMap.
      </small>
    </section>
  );
}
