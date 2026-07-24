'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import type { Session } from '@supabase/supabase-js';

import { supabase } from '../../lib/supabase';

const steps = ['Perfil', 'Vehículos', 'Resultado'];
const apiUrl =
  process.env.NEXT_PUBLIC_IICA_API_URL ||
  (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : '');

type City = {
  id: string;
  code: string;
  name: string;
};

type Vehicle = {
  id: string;
  brand: string;
  model: string;
  trim: string;
  model_year: number;
  powertrain: string;
  list_price: string;
  currency_code: string;
  safety_score: string;
};

type BuyerProfile = {
  cityCode: string;
  primaryUse: string;
  budget: number;
  annualKilometers: number;
  ownershipYears: number;
  householdSize: number;
  frequentRoadTrips: boolean;
  chargingAccess: string;
};

type EvaluationResult = {
  id: string;
  name: string;
  score: string;
  classification: string;
  strengths: string[];
  weaknesses: string[];
  influences: { key: string; direction: number; summary: string }[];
  recommendations: string[];
  engine_version: string;
  data_version: string;
};

type Evaluation = {
  city: string;
  evaluated_at: string;
  results: EvaluationResult[];
};

function parseNumber(value: FormDataEntryValue | null) {
  return Number(String(value ?? '').replace(/\D/g, ''));
}

function vehicleLabel(vehicle: Vehicle) {
  return `${vehicle.brand} ${vehicle.model} ${vehicle.trim} ${vehicle.model_year}`;
}

function formatPrice(vehicle: Vehicle) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: vehicle.currency_code,
    maximumFractionDigits: 0,
  }).format(Number(vehicle.list_price));
}

export default function CalculatorPage() {
  const [step, setStep] = useState(1);
  const [cities, setCities] = useState<City[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [profile, setProfile] = useState<BuyerProfile | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [catalogError, setCatalogError] = useState('');
  const [evaluationError, setEvaluationError] = useState('');
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [session, setSession] = useState<Session | null>(null);
  const [loginEmail, setLoginEmail] = useState('');
  const [authMessage, setAuthMessage] = useState('');
  const [history, setHistory] = useState<Evaluation[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    if (!supabase) return;
    void supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });
    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!session || !apiUrl) {
      setHistory([]);
      return;
    }
    let active = true;
    setHistoryLoading(true);
    void fetch(`${apiUrl}/v1/me/evaluations`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
    })
      .then(async (response) => {
        if (!response.ok) throw new Error('No fue posible consultar el historial.');
        return response.json() as Promise<Evaluation[]>;
      })
      .then((records) => {
        if (active) setHistory(records);
      })
      .catch(() => {
        if (active) setAuthMessage('No pudimos cargar tu historial.');
      })
      .finally(() => {
        if (active) setHistoryLoading(false);
      });
    return () => {
      active = false;
    };
  }, [session]);

  useEffect(() => {
    async function loadCatalog() {
      if (!apiUrl) {
        setCatalogError(
          'El servicio de cálculo todavía no está configurado en este despliegue.',
        );
        setLoadingCatalog(false);
        return;
      }
      try {
        const [citiesResponse, vehiclesResponse] = await Promise.all([
          fetch(`${apiUrl}/v1/countries/CO/cities`),
          fetch(`${apiUrl}/v1/vehicles?limit=100`),
        ]);
        if (!citiesResponse.ok || !vehiclesResponse.ok) {
          throw new Error('El catálogo no respondió correctamente.');
        }
        const [availableCities, availableVehicles] = await Promise.all([
          citiesResponse.json() as Promise<City[]>,
          vehiclesResponse.json() as Promise<Vehicle[]>,
        ]);
        setCities(availableCities);
        setVehicles(availableVehicles);
        if (!availableCities.length || !availableVehicles.length) {
          setCatalogError(
            'El catálogo aún no tiene ciudades y vehículos verificados disponibles.',
          );
        }
      } catch {
        setCatalogError(
          'No pudimos conectar con el servicio IICA. Intenta de nuevo en unos segundos.',
        );
      } finally {
        setLoadingCatalog(false);
      }
    }

    void loadCatalog();
  }, []);

  function startEvaluation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setProfile({
      cityCode: String(data.get('city')),
      primaryUse: String(data.get('use')),
      budget: parseNumber(data.get('budget')),
      annualKilometers: parseNumber(data.get('kilometers')),
      ownershipYears: Number(data.get('ownership-years')),
      householdSize: Number(data.get('household-size')),
      frequentRoadTrips: data.get('frequent-road-trips') === 'on',
      chargingAccess: String(data.get('charging-access')),
    });
    setEvaluationError('');
    setStep(2);
  }

  async function addCandidates(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profile) return;

    const data = new FormData(event.currentTarget);
    const selectedVehicles = [data.get('vehicle-one'), data.get('vehicle-two')]
      .map(String)
      .filter(Boolean);
    if (new Set(selectedVehicles).size !== selectedVehicles.length) {
      setEvaluationError('Selecciona dos versiones diferentes para compararlas.');
      return;
    }

    setCalculating(true);
    setEvaluationError('');
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (session) headers.Authorization = `Bearer ${session.access_token}`;
      const response = await fetch(`${apiUrl}/v1/evaluations`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          city_code: profile.cityCode,
          budget: profile.budget,
          annual_kilometers: profile.annualKilometers,
          ownership_years: profile.ownershipYears,
          primary_use: profile.primaryUse,
          household_size: profile.householdSize,
          frequent_road_trips: profile.frequentRoadTrips,
          charging_access: profile.chargingAccess,
          vehicle_ids: selectedVehicles,
        }),
      });
      const payload = (await response.json()) as Evaluation | { detail?: string };
      if (!response.ok) {
        throw new Error(
          'detail' in payload && payload.detail
            ? payload.detail
            : 'No fue posible calcular el IICA.',
        );
      }
      setEvaluation(payload as Evaluation);
      if (session) {
        setHistory((current) => [payload as Evaluation, ...current].slice(0, 20));
      }
      setStep(3);
    } catch (error) {
      setEvaluationError(
        error instanceof Error
          ? error.message
          : 'No fue posible calcular el IICA en este momento.',
      );
    } finally {
      setCalculating(false);
    }
  }

  async function sendMagicLink() {
    if (!supabase || !loginEmail) return;
    setAuthMessage('');
    const { error } = await supabase.auth.signInWithOtp({
      email: loginEmail,
      options: { emailRedirectTo: window.location.href },
    });
    setAuthMessage(
      error
        ? 'No pudimos enviar el enlace de acceso.'
        : 'Revisa tu correo para abrir el enlace de acceso.',
    );
  }

  return (
    <main className="calculator-page" id="contenido-principal" tabIndex={-1}>
      <nav className="nav" aria-label="Navegación de la calculadora">
        <Link className="brand" href="/">
          <span className="brand-mark">I</span>IICA
        </Link>
        <span className="step-label">
          Perfil de compra · {step} de {steps.length}
        </span>
      </nav>
      <section className="calculator-shell">
        <aside>
          <p className="eyebrow">
            <span />
            Tu punto de partida
          </p>
          <h1>Cuéntanos cómo vives tu movilidad.</h1>
          <p>
            Cada respuesta modifica el resultado. El cálculo usa únicamente datos
            versionados y trazables.
          </p>
          <ol className="steps" aria-label="Progreso de la evaluación">
            {steps.map((label, index) => (
              <li
                aria-current={index + 1 === step ? 'step' : undefined}
                className={index + 1 === step ? 'active' : ''}
                key={label}
              >
                <span>0{index + 1}</span>
                {label}
              </li>
            ))}
          </ol>
        </aside>
        <div className="step-content" aria-live="polite">
          {step === 1 ? (
            <form className="profile-form" onSubmit={startEvaluation}>
              {supabase ? (
                <div className="account-panel">
                  {session ? (
                    <>
                      <span>Resultado asociado a {session.user.email}</span>
                      <div className="history-panel">
                        <strong>Comparaciones guardadas</strong>
                        {historyLoading ? <small>Cargando historial…</small> : null}
                        {!historyLoading && !history.length ? (
                          <small>Aún no tienes cálculos guardados.</small>
                        ) : null}
                        {history.slice(0, 5).map((record, index) => (
                          <button
                            className="history-item"
                            type="button"
                            key={`${record.evaluated_at}-${index}`}
                            onClick={() => {
                              setEvaluation(record);
                              setStep(3);
                            }}
                          >
                            <span>
                              {record.city} · {record.evaluated_at}
                            </span>
                            <small>
                              {record.results[0]?.name} ·{' '}
                              {Math.round(Number(record.results[0]?.score ?? 0))}/100
                            </small>
                          </button>
                        ))}
                      </div>
                      <button
                        className="text-button"
                        type="button"
                        onClick={() => void supabase?.auth.signOut()}
                      >
                        Cerrar sesión
                      </button>
                    </>
                  ) : (
                    <>
                      <label>
                        Correo para guardar tu historial <small>(opcional)</small>
                        <input
                          type="email"
                          value={loginEmail}
                          onChange={(event) => setLoginEmail(event.target.value)}
                          placeholder="tu@correo.com"
                        />
                      </label>
                      <button
                        className="text-button"
                        type="button"
                        onClick={() => void sendMagicLink()}
                      >
                        Enviarme un enlace de acceso
                      </button>
                    </>
                  )}
                  {authMessage ? <small>{authMessage}</small> : null}
                </div>
              ) : null}
              {catalogError ? <p className="form-error">{catalogError}</p> : null}
              <label>
                ¿Dónde usarás principalmente el vehículo?
                <select
                  name="city"
                  required
                  disabled={loadingCatalog || !cities.length}
                >
                  <option value="">
                    {loadingCatalog ? 'Cargando ciudades…' : 'Selecciona una ciudad'}
                  </option>
                  {cities.map((city) => (
                    <option value={city.code} key={city.id}>
                      {city.name}, Colombia
                    </option>
                  ))}
                </select>
              </label>
              <label>
                ¿Cuál será su uso principal?
                <select name="use" defaultValue="mixed">
                  <option value="urban">Ciudad</option>
                  <option value="mixed">Mixto</option>
                  <option value="road_trips">Viajes frecuentes</option>
                  <option value="family">Familia</option>
                  <option value="work">Trabajo</option>
                </select>
              </label>
              <div className="field-grid">
                <label>
                  Presupuesto estimado (COP)
                  <input
                    name="budget"
                    inputMode="numeric"
                    placeholder="Ej. 100.000.000"
                    required
                  />
                </label>
                <label>
                  Kilómetros al año
                  <input
                    name="kilometers"
                    inputMode="numeric"
                    placeholder="Ej. 12.000"
                    required
                  />
                </label>
                <label>
                  Años que planeas conservarlo
                  <input
                    name="ownership-years"
                    type="number"
                    min="1"
                    max="30"
                    defaultValue="5"
                    required
                  />
                </label>
                <label>
                  Personas en tu hogar
                  <input
                    name="household-size"
                    type="number"
                    min="1"
                    max="20"
                    defaultValue="1"
                    required
                  />
                </label>
              </div>
              <label>
                Acceso habitual a carga
                <select name="charging-access" defaultValue="none">
                  <option value="none">No tengo acceso</option>
                  <option value="home">En casa</option>
                  <option value="work">En el trabajo</option>
                  <option value="public">Solo carga pública</option>
                </select>
              </label>
              <label className="check">
                <input type="checkbox" name="frequent-road-trips" /> Hago viajes por
                carretera con frecuencia
              </label>
              <button
                className="button button-primary"
                type="submit"
                disabled={loadingCatalog || Boolean(catalogError)}
              >
                Continuar con mi perfil <span>→</span>
              </button>
            </form>
          ) : step === 2 ? (
            <form className="profile-form" onSubmit={addCandidates}>
              <p className="form-kicker">Paso 2 de 3</p>
              <h2>¿Qué versiones quieres comparar?</h2>
              <p className="form-copy">
                Solo aparecen versiones con precio, seguridad y señales de mercado
                verificadas.
              </p>
              {evaluationError ? (
                <p className="form-error" role="alert">
                  {evaluationError}
                </p>
              ) : null}
              <label>
                Primer vehículo
                <select name="vehicle-one" defaultValue="" required>
                  <option value="">Selecciona una versión</option>
                  {vehicles.map((vehicle) => (
                    <option value={vehicle.id} key={vehicle.id}>
                      {vehicleLabel(vehicle)} · {formatPrice(vehicle)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Segundo vehículo <small>(opcional)</small>
                <select name="vehicle-two" defaultValue="">
                  <option value="">Sin segundo vehículo</option>
                  {vehicles.map((vehicle) => (
                    <option value={vehicle.id} key={vehicle.id}>
                      {vehicleLabel(vehicle)} · {formatPrice(vehicle)}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="button button-primary"
                type="submit"
                disabled={calculating}
              >
                {calculating ? 'Calculando…' : 'Calcular mi IICA'}{' '}
                <span aria-hidden="true">→</span>
              </button>
              <button className="text-button" type="button" onClick={() => setStep(1)}>
                ← Volver al perfil
              </button>
            </form>
          ) : evaluation ? (
            <section className="profile-form results">
              <p className="form-kicker">Resultado en {evaluation.city}</p>
              <h2>Tu IICA está listo.</h2>
              <p className="form-copy">
                Calculado con reglas y datos vigentes al {evaluation.evaluated_at}.
              </p>
              <div className="result-list">
                {evaluation.results.map((result, index) => (
                  <article className="result-card" key={result.id}>
                    {evaluation.results.length > 1 && index === 0 ? (
                      <span className="result-winner">Mejor ajuste</span>
                    ) : null}
                    <p>{result.name}</p>
                    <div className="result-score">
                      <strong>{Math.round(Number(result.score))}</strong>
                      <span>/100</span>
                    </div>
                    <h3>{result.classification}</h3>
                    <h4>Lo que más influyó</h4>
                    <ul>
                      {result.influences.map((influence) => (
                        <li key={influence.key}>{influence.summary}</li>
                      ))}
                    </ul>
                    {result.weaknesses.length ? (
                      <>
                        <h4>Debes considerar</h4>
                        <ul>
                          {result.weaknesses.map((weakness) => (
                            <li key={weakness}>{weakness}</li>
                          ))}
                        </ul>
                      </>
                    ) : null}
                    <p className="result-recommendation">{result.recommendations[0]}</p>
                    <small>
                      Motor {result.engine_version} · Datos {result.data_version}
                    </small>
                  </article>
                ))}
              </div>
              <button className="text-button" type="button" onClick={() => setStep(2)}>
                ← Editar vehículos
              </button>
            </section>
          ) : null}
        </div>
      </section>
    </main>
  );
}
