'use client';

import type {
  LayerGroup,
  LeafletMouseEvent,
  Map as LeafletMap,
  Marker,
  Polyline,
} from 'leaflet';
import type { KeyboardEvent } from 'react';
import { useEffect, useMemo, useRef, useState } from 'react';

type PlaceCategory = 'home' | 'work' | 'study' | 'care' | 'frequent' | 'other';

type Place = {
  id: string;
  name: string;
  address: string;
  category: PlaceCategory;
  lat: number;
  lng: number;
};

type SearchCandidate = {
  id: string;
  name: string;
  display_name: string;
  latitude: number;
  longitude: number;
  category: string | null;
};

type Journey = {
  id: string;
  originId: string;
  destinationId: string;
  frequencyPerWeek: number;
  weeksPerYear: number;
  roundTrip: boolean;
  byCar: boolean;
};

type DistanceSource = 'route' | 'approximate';

type RouteResult = {
  distanceKilometers: number;
  durationMinutes: number | null;
  geometry: [number, number][];
  source: DistanceSource;
};

type MobilityEstimate = {
  annualKilometers: number | null;
  annualMinutes: number | null;
  source: DistanceSource | null;
};

type ManualPlacement = {
  name: string;
  category: PlaceCategory;
};

type MobilityMapProps = {
  apiUrl: string;
  center: [number, number];
  cityCode: string;
  cityName: string;
  ownershipYears: number;
  onEstimateChange: (estimate: MobilityEstimate) => void;
  onPlaceCountChange: (count: number) => void;
  onUseEstimate: (annualKilometers: number) => void;
};

type OsrmResponse = {
  routes?: {
    distance: number;
    duration: number;
    geometry: { coordinates: [number, number][] };
  }[];
};

const categories: { id: PlaceCategory; label: string; shortLabel: string }[] = [
  { id: 'home', label: 'Casa', shortLabel: 'Casa' },
  { id: 'work', label: 'Trabajo', shortLabel: 'Trabajo' },
  { id: 'study', label: 'Estudio', shortLabel: 'Estudio' },
  { id: 'care', label: 'Familia o cuidado', shortLabel: 'Cuidado' },
  { id: 'frequent', label: 'Lugar frecuente', shortLabel: 'Frecuente' },
  { id: 'other', label: 'Otro', shortLabel: 'Otro' },
];

const routeColors = ['#d9ff65', '#ffb86b', '#79dfff', '#f39ac7', '#c8a7ff'];

function categoryLabel(category: PlaceCategory) {
  return (
    categories.find((candidate) => candidate.id === category)?.shortLabel ?? 'Lugar'
  );
}

function approximateDistance(start: Place, end: Place) {
  const earthRadiusKm = 6371;
  const latitudeDelta = ((end.lat - start.lat) * Math.PI) / 180;
  const longitudeDelta = ((end.lng - start.lng) * Math.PI) / 180;
  const startLatitude = (start.lat * Math.PI) / 180;
  const endLatitude = (end.lat * Math.PI) / 180;
  const haversine =
    Math.sin(latitudeDelta / 2) ** 2 +
    Math.cos(startLatitude) * Math.cos(endLatitude) * Math.sin(longitudeDelta / 2) ** 2;
  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine));
}

function createId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function MobilityMap({
  apiUrl,
  center,
  cityCode,
  cityName,
  ownershipYears,
  onEstimateChange,
  onPlaceCountChange,
  onUseEstimate,
}: MobilityMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const markersRef = useRef<LayerGroup | null>(null);
  const routesRef = useRef<LayerGroup | null>(null);
  const leafletRef = useRef<typeof import('leaflet') | null>(null);
  const routeRequestRef = useRef<AbortController | null>(null);
  const searchRequestRef = useRef<AbortController | null>(null);
  const manualPlacementRef = useRef<ManualPlacement | null>(null);
  const centerRef = useRef(center);
  const [mapReady, setMapReady] = useState(false);
  const [places, setPlaces] = useState<Place[]>([]);
  const [journeys, setJourneys] = useState<Journey[]>([]);
  const [routeResults, setRouteResults] = useState<Record<string, RouteResult>>({});
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<PlaceCategory>('home');
  const [searchResults, setSearchResults] = useState<SearchCandidate[]>([]);
  const [searchStatus, setSearchStatus] = useState(
    'Busca un lugar para comenzar a dibujar tu semana.',
  );
  const [searching, setSearching] = useState(false);
  const [manualFallbackAvailable, setManualFallbackAvailable] = useState(false);
  const [manualPlacementActive, setManualPlacementActive] = useState(false);
  const [originId, setOriginId] = useState('');
  const [destinationId, setDestinationId] = useState('');
  const [frequencyPerWeek, setFrequencyPerWeek] = useState(5);
  const [weeksPerYear, setWeeksPerYear] = useState(48);
  const [roundTrip, setRoundTrip] = useState(true);
  const [byCar, setByCar] = useState(true);
  const [journeyMessage, setJourneyMessage] = useState('');

  centerRef.current = center;

  useEffect(() => {
    let active = true;

    async function initializeMap() {
      if (!containerRef.current || mapRef.current) return;
      const L = await import('leaflet');
      if (!active || !containerRef.current) return;

      leafletRef.current = L;
      const map = L.map(containerRef.current, {
        scrollWheelZoom: true,
        zoomControl: true,
      }).setView(centerRef.current, 13);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution:
          '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);
      routesRef.current = L.layerGroup().addTo(map);
      markersRef.current = L.layerGroup().addTo(map);
      mapRef.current = map;
      setMapReady(true);
    }

    void initializeMap();
    return () => {
      active = false;
      routeRequestRef.current?.abort();
      searchRequestRef.current?.abort();
      mapRef.current?.remove();
      mapRef.current = null;
      leafletRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!mapReady || !map) return;

    function handleManualPlacement(event: LeafletMouseEvent) {
      const pending = manualPlacementRef.current;
      if (!pending) return;
      if (places.length >= 8) {
        manualPlacementRef.current = null;
        setManualPlacementActive(false);
        setSearchStatus(
          'Llegaste al máximo recomendado de 8 lugares. Elimina uno para continuar.',
        );
        return;
      }

      const place: Place = {
        id: createId('manual-place'),
        name: pending.name,
        address: `Ubicación ajustada manualmente en ${cityName}`,
        category: pending.category,
        lat: event.latlng.lat,
        lng: event.latlng.lng,
      };
      const nextPlaces = [...places, place];
      setPlaces(nextPlaces);
      setOriginId((current) => current || nextPlaces[0]?.id || '');
      setDestinationId(place.id);
      setCategory(nextPlaces.length === 1 ? 'work' : 'frequent');
      setQuery('');
      setSearchResults([]);
      setManualFallbackAvailable(false);
      setManualPlacementActive(false);
      manualPlacementRef.current = null;
      setSearchStatus(
        `${place.name} agregado en el punto exacto que marcaste. Puedes arrastrar el pin para afinarlo.`,
      );
    }

    map.on('click', handleManualPlacement);
    return () => {
      map.off('click', handleManualPlacement);
    };
  }, [cityName, mapReady, places]);

  useEffect(() => {
    if (!containerRef.current || !mapRef.current) return;
    const map = mapRef.current;
    const observer = new ResizeObserver(() => map.invalidateSize(false));
    observer.observe(containerRef.current);
    const timeout = window.setTimeout(() => map.invalidateSize(false), 120);
    return () => {
      window.clearTimeout(timeout);
      observer.disconnect();
    };
  }, [mapReady]);

  useEffect(() => {
    searchRequestRef.current?.abort();
    setPlaces([]);
    setJourneys([]);
    setRouteResults({});
    setSearchResults([]);
    setQuery('');
    setCategory('home');
    setSearching(false);
    setManualFallbackAvailable(false);
    setManualPlacementActive(false);
    manualPlacementRef.current = null;
    setSearchStatus('Busca un lugar para comenzar a dibujar tu semana.');
    setJourneyMessage('');
    onEstimateChange({
      annualKilometers: null,
      annualMinutes: null,
      source: null,
    });
    onPlaceCountChange(0);
    mapRef.current?.setView(center, 13);
  }, [center, cityCode, onEstimateChange, onPlaceCountChange]);

  useEffect(() => {
    onPlaceCountChange(places.length);
  }, [onPlaceCountChange, places.length]);

  useEffect(() => {
    const L = leafletRef.current;
    const markerLayer = markersRef.current;
    const map = mapRef.current;
    if (!mapReady || !L || !markerLayer || !map) return;

    markerLayer.clearLayers();
    places.forEach((place, index) => {
      const marker: Marker = L.marker([place.lat, place.lng], {
        draggable: true,
        title: `${categoryLabel(place.category)}: ${place.name}`,
        icon: L.divIcon({
          className: `route-marker route-marker--${place.category}`,
          html: `<span>${index + 1}</span>`,
          iconAnchor: [18, 18],
          iconSize: [36, 36],
        }),
      }).addTo(markerLayer);
      marker.on('dragend', () => {
        const location = marker.getLatLng();
        setPlaces((current) =>
          current.map((candidate) =>
            candidate.id === place.id
              ? { ...candidate, lat: location.lat, lng: location.lng }
              : candidate,
          ),
        );
        setSearchStatus(`${place.name} fue ajustado. Recalcularemos sus trayectos.`);
      });
    });

    if (!places.length) {
      map.setView(center, 13);
    } else if (places.length === 1) {
      map.setView([places[0].lat, places[0].lng], 15);
    } else {
      map.fitBounds(L.latLngBounds(places.map((place) => [place.lat, place.lng])), {
        maxZoom: 15,
        padding: [54, 54],
      });
    }
  }, [center, mapReady, places]);

  useEffect(() => {
    const routeLayer = routesRef.current;
    const L = leafletRef.current;
    if (!mapReady || !routeLayer || !L) return;

    routeLayer.clearLayers();
    journeys.forEach((journey, index) => {
      const route = routeResults[journey.id];
      if (!route) return;
      const options = journey.byCar ? undefined : '8 8';
      const halo: Polyline = L.polyline(route.geometry, {
        color: '#11120f',
        opacity: 0.78,
        weight: 9,
        dashArray: options,
      });
      const line: Polyline = L.polyline(route.geometry, {
        color: routeColors[index % routeColors.length],
        opacity: journey.byCar ? 0.95 : 0.7,
        weight: 5,
        dashArray: options,
      });
      halo.addTo(routeLayer);
      line.addTo(routeLayer);
    });
  }, [journeys, mapReady, routeResults]);

  useEffect(() => {
    routeRequestRef.current?.abort();
    if (!journeys.length) {
      setRouteResults({});
      return;
    }

    const controller = new AbortController();
    routeRequestRef.current = controller;
    const placeById = new Map(places.map((place) => [place.id, place]));

    async function calculateRoutes() {
      const nextResults: Record<string, RouteResult> = {};
      for (const journey of journeys) {
        const origin = placeById.get(journey.originId);
        const destination = placeById.get(journey.destinationId);
        if (!origin || !destination) continue;
        try {
          const coordinates = `${origin.lng},${origin.lat};${destination.lng},${destination.lat}`;
          const response = await fetch(
            `https://router.project-osrm.org/route/v1/driving/${coordinates}?overview=full&geometries=geojson`,
            { signal: controller.signal },
          );
          if (!response.ok) throw new Error('route-unavailable');
          const payload = (await response.json()) as OsrmResponse;
          const route = payload.routes?.[0];
          if (!route) throw new Error('route-unavailable');
          nextResults[journey.id] = {
            distanceKilometers: route.distance / 1000,
            durationMinutes: route.duration / 60,
            geometry: route.geometry.coordinates.map(
              ([longitude, latitude]) => [latitude, longitude] as [number, number],
            ),
            source: 'route',
          };
        } catch (error: unknown) {
          if (error instanceof DOMException && error.name === 'AbortError') return;
          nextResults[journey.id] = {
            distanceKilometers: approximateDistance(origin, destination) * 1.25,
            durationMinutes: null,
            geometry: [
              [origin.lat, origin.lng],
              [destination.lat, destination.lng],
            ],
            source: 'approximate',
          };
        }
        if (!controller.signal.aborted) {
          setRouteResults({ ...nextResults });
        }
      }
    }

    void calculateRoutes();
    return () => controller.abort();
  }, [journeys, places]);

  const estimate = useMemo<MobilityEstimate>(() => {
    const vehicleJourneys = journeys.filter((journey) => journey.byCar);
    if (!vehicleJourneys.length) {
      return {
        annualKilometers: null,
        annualMinutes: null,
        source: null,
      };
    }

    let annualKilometers = 0;
    let annualMinutes = 0;
    let hasMissingDuration = false;
    let hasApproximateRoute = false;
    for (const journey of vehicleJourneys) {
      const route = routeResults[journey.id];
      if (!route) {
        return {
          annualKilometers: null,
          annualMinutes: null,
          source: null,
        };
      }
      const multiplier =
        journey.frequencyPerWeek * journey.weeksPerYear * (journey.roundTrip ? 2 : 1);
      annualKilometers += route.distanceKilometers * multiplier;
      if (route.durationMinutes === null) {
        hasMissingDuration = true;
      } else {
        annualMinutes += route.durationMinutes * multiplier;
      }
      if (route.source === 'approximate') hasApproximateRoute = true;
    }
    return {
      annualKilometers: Math.round(annualKilometers),
      annualMinutes: hasMissingDuration ? null : Math.round(annualMinutes),
      source: hasApproximateRoute ? 'approximate' : 'route',
    };
  }, [journeys, routeResults]);

  useEffect(() => {
    onEstimateChange(estimate);
  }, [estimate, onEstimateChange]);

  async function searchPlaces() {
    const normalizedQuery = query.trim();
    if (normalizedQuery.length < 3 || searching) return;
    if (!apiUrl) {
      setSearchStatus('El buscador de lugares aún no está configurado.');
      return;
    }

    searchRequestRef.current?.abort();
    const controller = new AbortController();
    searchRequestRef.current = controller;
    setSearching(true);
    setSearchResults([]);
    setManualFallbackAvailable(false);
    setSearchStatus(`Buscando “${normalizedQuery}” en ${cityName}…`);
    try {
      const response = await fetch(`${apiUrl}/v1/places/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: normalizedQuery,
          city_name: cityName,
        }),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error('search-unavailable');
      const candidates = (await response.json()) as SearchCandidate[];
      setSearchResults(candidates);
      setManualFallbackAvailable(true);
      setSearchStatus(
        candidates.length
          ? 'Elige el resultado correcto; no seleccionaremos uno por ti.'
          : 'No encontramos coincidencias. Prueba con dirección, barrio y municipio.',
      );
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === 'AbortError') return;
      setSearchStatus(
        'No pudimos consultar el buscador. Espera un momento e intenta de nuevo.',
      );
      setManualFallbackAvailable(true);
    } finally {
      if (!controller.signal.aborted) setSearching(false);
    }
  }

  function handleSearchKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    void searchPlaces();
  }

  function addPlace(candidate: SearchCandidate) {
    if (places.length >= 8) {
      setSearchStatus(
        'Llegaste al máximo recomendado de 8 lugares. Elimina uno para continuar.',
      );
      return;
    }
    if (places.some((place) => place.id === candidate.id)) {
      setSearchStatus('Ese lugar ya forma parte de tu mapa.');
      return;
    }

    const place: Place = {
      id: candidate.id,
      name: candidate.name,
      address: candidate.display_name,
      category,
      lat: candidate.latitude,
      lng: candidate.longitude,
    };
    const nextPlaces = [...places, place];
    setPlaces(nextPlaces);
    setSearchResults([]);
    setQuery('');
    setManualFallbackAvailable(false);
    setManualPlacementActive(false);
    manualPlacementRef.current = null;
    setCategory(nextPlaces.length === 1 ? 'work' : 'frequent');
    setOriginId((current) => current || nextPlaces[0]?.id || '');
    setDestinationId(place.id);
    setSearchStatus(
      `${place.name} agregado como ${categoryLabel(category)}. Puedes arrastrar el pin para afinarlo.`,
    );
  }

  function startManualPlacement() {
    const name = query.trim();
    if (name.length < 3) return;
    manualPlacementRef.current = { name, category };
    setManualPlacementActive(true);
    setSearchResults([]);
    setSearchStatus(
      `Haz clic sobre la ubicación exacta de “${name}” en el mapa. Después podrás arrastrar el pin.`,
    );
    containerRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    });
  }

  function cancelManualPlacement() {
    manualPlacementRef.current = null;
    setManualPlacementActive(false);
    setSearchStatus('Ubicación manual cancelada. Puedes intentar otra búsqueda.');
  }

  function removePlace(placeId: string) {
    setPlaces((current) => current.filter((place) => place.id !== placeId));
    setJourneys((current) =>
      current.filter(
        (journey) => journey.originId !== placeId && journey.destinationId !== placeId,
      ),
    );
    setOriginId((current) => (current === placeId ? '' : current));
    setDestinationId((current) => (current === placeId ? '' : current));
  }

  function addJourney() {
    if (!originId || !destinationId || originId === destinationId) {
      setJourneyMessage('Selecciona dos lugares diferentes.');
      return;
    }
    const duplicate = journeys.some(
      (journey) =>
        journey.originId === originId &&
        journey.destinationId === destinationId &&
        journey.roundTrip === roundTrip,
    );
    if (duplicate) {
      setJourneyMessage('Ese trayecto ya está en tu semana.');
      return;
    }
    setJourneys((current) => [
      ...current,
      {
        id: createId('journey'),
        originId,
        destinationId,
        frequencyPerWeek,
        weeksPerYear,
        roundTrip,
        byCar,
      },
    ]);
    setJourneyMessage('Trayecto agregado. Estamos calculando su ruta.');
  }

  function placeName(placeId: string) {
    return places.find((place) => place.id === placeId)?.name ?? 'Lugar';
  }

  const annualHours =
    estimate.annualMinutes === null ? null : Math.round(estimate.annualMinutes / 60);
  const lifetimeKilometers =
    estimate.annualKilometers === null
      ? null
      : estimate.annualKilometers * ownershipYears;
  const lifetimeDrivingDays =
    estimate.annualMinutes === null
      ? null
      : Math.round((estimate.annualMinutes * ownershipYears) / 60 / 24);

  return (
    <section className="mobility-map" aria-labelledby="mobility-map-title">
      <header className="map-heading">
        <div>
          <span className="map-kicker">Tu mapa de vida</span>
          <h2 id="mobility-map-title">
            Haz visible la rutina que el vehículo tendrá que sostener.
          </h2>
          <p>
            Busca tus lugares reales, conecta cada trayecto y dinos con qué frecuencia
            ocurre. El mapa traduce esa semana en una decisión anual.
          </p>
        </div>
        <span className="point-counter">{places.length}/8 lugares</span>
      </header>

      <div className="map-studio">
        <div className="map-stage">
          <div
            className={`map-canvas ${
              manualPlacementActive ? 'map-canvas--placing' : ''
            }`}
            ref={containerRef}
            aria-label={`Mapa interactivo de ${cityName} con tus lugares y trayectos`}
          />
          <div className="map-stage-note">
            <strong>
              {manualPlacementActive ? 'Marca el punto exacto' : cityName}
            </strong>
            <span>
              {manualPlacementActive
                ? 'Haz clic en el edificio; el mapa colocará un pin editable.'
                : 'Arrastra cualquier pin para afinar su ubicación.'}
            </span>
          </div>
        </div>

        <aside className="places-panel" aria-label="Buscador y lugares de tu mapa">
          <div className="place-search">
            <span className="panel-step">1 · Encuentra un lugar</span>
            <fieldset>
              <legend>¿Qué representa en tu vida?</legend>
              <div className="place-category-grid">
                {categories.map((option) => (
                  <label
                    className={category === option.id ? 'selected' : ''}
                    key={option.id}
                  >
                    <input
                      type="radio"
                      name="map-place-category"
                      checked={category === option.id}
                      onChange={() => setCategory(option.id)}
                    />
                    {option.label}
                  </label>
                ))}
              </div>
            </fieldset>
            <label htmlFor="place-search-input">
              Dirección o nombre del lugar
              <span className="search-input-row">
                <input
                  id="place-search-input"
                  type="search"
                  value={query}
                  minLength={3}
                  maxLength={160}
                  autoComplete="off"
                  placeholder={`Ej. Parque del Poblado, ${cityName}`}
                  onChange={(event) => {
                    setQuery(event.target.value);
                    setManualFallbackAvailable(false);
                    if (manualPlacementRef.current) cancelManualPlacement();
                  }}
                  onKeyDown={handleSearchKeyDown}
                />
                <button
                  className="search-button"
                  type="button"
                  disabled={query.trim().length < 3 || searching}
                  onClick={() => void searchPlaces()}
                >
                  {searching ? 'Buscando…' : 'Buscar'}
                </button>
              </span>
            </label>
            <p className="search-status" aria-live="polite">
              {searchStatus}
            </p>
            {searchResults.length ? (
              <ul className="search-results" aria-label="Resultados de lugares">
                {searchResults.map((candidate) => (
                  <li key={candidate.id}>
                    <button type="button" onClick={() => addPlace(candidate)}>
                      <strong>{candidate.name}</strong>
                      <span>{candidate.display_name}</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
            {manualPlacementActive ? (
              <div className="manual-placement-prompt">
                <strong>El mapa está listo para recibir tu punto.</strong>
                <span>Haz clic en el edificio o cancela para volver a buscar.</span>
                <button type="button" onClick={cancelManualPlacement}>
                  Cancelar ubicación manual
                </button>
              </div>
            ) : manualFallbackAvailable ? (
              <button
                className="manual-place-button"
                type="button"
                onClick={startManualPlacement}
              >
                <strong>¿No aparece “{query.trim()}”?</strong>
                <span>Ubícalo con un clic exacto sobre el mapa →</span>
              </button>
            ) : null}
          </div>

          <div className="places-list">
            <span className="panel-step">Tus lugares</span>
            {!places.length ? (
              <p className="empty-panel">
                Tu mapa está listo. Agrega casa, trabajo y los lugares que de verdad
                condicionan tus días.
              </p>
            ) : (
              <ol>
                {places.map((place, index) => (
                  <li key={place.id}>
                    <span className={`place-number place-number--${place.category}`}>
                      {index + 1}
                    </span>
                    <span>
                      <small>{categoryLabel(place.category)}</small>
                      <strong>{place.name}</strong>
                      <span>{place.address}</span>
                    </span>
                    <button
                      type="button"
                      aria-label={`Eliminar ${place.name}`}
                      onClick={() => removePlace(place.id)}
                    >
                      ×
                    </button>
                  </li>
                ))}
              </ol>
            )}
          </div>
        </aside>
      </div>

      {places.length >= 2 ? (
        <section className="journey-studio" aria-labelledby="journey-studio-title">
          <div className="journey-heading">
            <div>
              <span className="panel-step">2 · Construye una semana real</span>
              <h3 id="journey-studio-title">Conecta tus lugares</h3>
            </div>
            <p>Cada conexión tiene su propia frecuencia. Así evitamos inflar tus km.</p>
          </div>
          <div className="journey-builder">
            <label>
              Desde
              <select
                value={originId}
                onChange={(event) => setOriginId(event.target.value)}
              >
                <option value="">Elige un origen</option>
                {places.map((place) => (
                  <option value={place.id} key={place.id}>
                    {categoryLabel(place.category)} · {place.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Hasta
              <select
                value={destinationId}
                onChange={(event) => setDestinationId(event.target.value)}
              >
                <option value="">Elige un destino</option>
                {places.map((place) => (
                  <option value={place.id} key={place.id}>
                    {categoryLabel(place.category)} · {place.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Veces por semana
              <input
                type="number"
                min="0.5"
                max="21"
                step="0.5"
                value={frequencyPerWeek}
                onChange={(event) =>
                  setFrequencyPerWeek(Number(event.target.value) || 0.5)
                }
              />
            </label>
            <label>
              Semanas al año
              <input
                type="number"
                min="1"
                max="52"
                value={weeksPerYear}
                onChange={(event) => setWeeksPerYear(Number(event.target.value) || 1)}
              />
            </label>
          </div>
          <div className="journey-options">
            <label className="check">
              <input
                type="checkbox"
                checked={roundTrip}
                onChange={(event) => setRoundTrip(event.target.checked)}
              />
              Incluye regreso
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={byCar}
                onChange={(event) => setByCar(event.target.checked)}
              />
              Lo haría en el vehículo evaluado
            </label>
            <button className="add-journey-button" type="button" onClick={addJourney}>
              Agregar trayecto <span aria-hidden="true">→</span>
            </button>
          </div>
          {journeyMessage ? (
            <p className="journey-message" aria-live="polite">
              {journeyMessage}
            </p>
          ) : null}
          {journeys.length ? (
            <ul className="journey-list">
              {journeys.map((journey, index) => {
                const route = routeResults[journey.id];
                return (
                  <li key={journey.id}>
                    <span
                      className="journey-line"
                      style={{
                        background: routeColors[index % routeColors.length],
                      }}
                    />
                    <span>
                      <strong>
                        {placeName(journey.originId)} →{' '}
                        {placeName(journey.destinationId)}
                      </strong>
                      <small>
                        {journey.roundTrip ? 'Ida y regreso' : 'Solo ida'} ·{' '}
                        {journey.frequencyPerWeek}×/sem · {journey.weeksPerYear} sem/año
                        {!journey.byCar ? ' · excluido del cálculo del vehículo' : ''}
                      </small>
                    </span>
                    <span className="journey-distance">
                      {route
                        ? `${route.distanceKilometers.toFixed(1)} km`
                        : 'Calculando…'}
                    </span>
                    <button
                      type="button"
                      aria-label={`Eliminar trayecto de ${placeName(
                        journey.originId,
                      )} a ${placeName(journey.destinationId)}`}
                      onClick={() =>
                        setJourneys((current) =>
                          current.filter((candidate) => candidate.id !== journey.id),
                        )
                      }
                    >
                      ×
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : null}
        </section>
      ) : null}

      <section className="mobility-story" aria-labelledby="mobility-story-title">
        <div>
          <span className="panel-step">3 · Lo que significa para tu decisión</span>
          <h3 id="mobility-story-title">La huella de tu rutina</h3>
          <p>
            {estimate.annualKilometers === null
              ? 'Agrega al menos un trayecto para convertir tu semana en una estimación anual.'
              : `Solo esta rutina podría sumar ${lifetimeKilometers?.toLocaleString(
                  'es-CO',
                )} km durante los ${ownershipYears} años que planeas conservar el vehículo.`}
          </p>
        </div>
        <div className="mobility-metrics">
          <article>
            <span>Distancia anual</span>
            <strong>
              {estimate.annualKilometers === null
                ? '—'
                : `${estimate.annualKilometers.toLocaleString('es-CO')} km`}
            </strong>
          </article>
          <article>
            <span>Tiempo anual sin tráfico</span>
            <strong>{annualHours === null ? '—' : `${annualHours} h`}</strong>
          </article>
          <article>
            <span>Días al volante en {ownershipYears} años</span>
            <strong>
              {lifetimeDrivingDays === null ? '—' : `≈ ${lifetimeDrivingDays}`}
            </strong>
          </article>
        </div>
        {estimate.annualKilometers !== null ? (
          <button
            className="map-use-button"
            type="button"
            onClick={() => onUseEstimate(estimate.annualKilometers ?? 0)}
          >
            Usar {estimate.annualKilometers.toLocaleString('es-CO')} km/año en mi perfil{' '}
            <span aria-hidden="true">→</span>
          </button>
        ) : null}
        {estimate.source === 'approximate' ? (
          <small>
            Una o más distancias son aproximadas porque el servicio vial no respondió.
          </small>
        ) : null}
      </section>

      <p className="map-privacy">
        Privacidad: “Casa”, “Trabajo” y tus trayectos viven solo en esta sesión y no se
        guardan en tu historial. La búsqueda se envía a OpenStreetMap y las coordenadas
        al servicio vial; no incluyas nombres de personas ni notas privadas.{' '}
        <a
          href="https://www.openstreetmap.org/copyright"
          target="_blank"
          rel="noreferrer"
        >
          Búsqueda y datos © OpenStreetMap contributors
        </a>
        .
      </p>
    </section>
  );
}
