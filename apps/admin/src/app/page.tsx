'use client';

import type { Session } from '@supabase/supabase-js';
import { FormEvent, useCallback, useEffect, useState } from 'react';

import { AdminForms } from '../components/admin-forms';
import { supabase } from '../lib/supabase';

const apiUrl =
  process.env.NEXT_PUBLIC_IICA_API_URL ||
  (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : '');

const sections = [
  ['Catálogo', 'Marcas, modelos y versiones', 'vehicle_brands'],
  ['Territorio', 'Países, departamentos y ciudades', 'countries'],
  ['Reglas locales', 'Impuestos, incentivos y movilidad', 'incentives'],
  ['Infraestructura', 'Carga, talleres y concesionarios', 'infrastructure_snapshots'],
];

type Counts = Record<string, number | null>;

export default function AdminHome() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [counts, setCounts] = useState<Counts>({});
  const [sendingLink, setSendingLink] = useState(false);

  const loadCounts = useCallback(async () => {
    const endpoints = {
      vehicle_brands: '/v1/vehicle-brands',
      countries: '/v1/countries',
      tax_rules: '/v1/tax-rules',
      incentives: '/v1/incentives',
      infrastructure_snapshots: null,
    };
    const entries = await Promise.all(
      Object.entries(endpoints).map(async ([key, endpoint]) => {
        if (!endpoint) return [key, null] as const;
        try {
          const response = await fetch(`${apiUrl}${endpoint}`);
          if (!response.ok) return [key, null] as const;
          const records = (await response.json()) as unknown[];
          return [key, records.length] as const;
        } catch {
          return [key, null] as const;
        }
      }),
    );
    setCounts(Object.fromEntries(entries));
  }, []);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }
    void supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });
    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (session) void loadCounts();
  }, [loadCounts, session]);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supabase) return;
    setMessage('');
    const form = new FormData(event.currentTarget);
    const { error } = await supabase.auth.signInWithPassword({
      email: String(form.get('email')),
      password: String(form.get('password')),
    });
    if (error) setMessage('No fue posible iniciar sesión. Revisa tus credenciales.');
  }

  async function sendMagicLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supabase) return;
    setMessage('');
    setSendingLink(true);
    const form = new FormData(event.currentTarget);
    const { error } = await supabase.auth.signInWithOtp({
      email: String(form.get('email')),
      options: {
        emailRedirectTo: `${window.location.origin}/`,
      },
    });
    setSendingLink(false);
    setMessage(
      error
        ? 'No fue posible enviar el enlace. Verifica el correo e inténtalo de nuevo.'
        : 'Revisa tu correo: enviamos un enlace seguro para entrar.',
    );
  }

  if (loading) {
    return <main className="admin-state">Validando sesión…</main>;
  }

  if (!supabase) {
    return (
      <main className="admin-state">
        <p>Configuración pendiente</p>
        <h1>Conecta Supabase para habilitar la administración.</h1>
        <span>
          Define NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY durante
          el despliegue.
        </span>
      </main>
    );
  }

  if (!session) {
    return (
      <main className="login-shell" id="contenido-principal">
        <div className="login-card">
          <p>IICA Admin</p>
          <h1>Datos verificables, acceso controlado.</h1>
          <form className="login-method" onSubmit={sendMagicLink}>
            <label>
              Correo administrativo
              <input type="email" name="email" autoComplete="email" required />
            </label>
            <button type="submit" disabled={sendingLink}>
              {sendingLink ? 'Enviando…' : 'Recibir enlace de acceso'}
            </button>
          </form>
          <details>
            <summary>Entrar con contraseña</summary>
            <form className="login-method" onSubmit={signIn}>
              <label>
                Correo
                <input type="email" name="email" autoComplete="email" required />
              </label>
              <label>
                Contraseña
                <input
                  type="password"
                  name="password"
                  autoComplete="current-password"
                  required
                />
              </label>
              <button type="submit">Iniciar sesión</button>
            </form>
          </details>
          {message ? <div className="admin-message">{message}</div> : null}
        </div>
      </main>
    );
  }

  return (
    <main className="admin">
      <aside>
        <a className="admin-brand" href="#contenido-principal">
          IICA <span>Admin</span>
        </a>
        <nav>
          {sections.map(([name]) => (
            <a href="#gestion" key={name}>
              {name}
            </a>
          ))}
        </nav>
        <button
          className="logout"
          type="button"
          onClick={() => void supabase?.auth.signOut()}
        >
          Cerrar sesión
        </button>
        <small>{session.user.email}</small>
      </aside>
      <section id="contenido-principal" tabIndex={-1}>
        <header>
          <div>
            <p>Administración</p>
            <h1>Datos que sostienen cada IICA.</h1>
          </div>
        </header>
        {message ? <div className="admin-message">{message}</div> : null}
        <AdminForms session={session} onComplete={loadCounts} onMessage={setMessage} />
        <div className="notice">
          Las reglas vigentes requieren fuente, ciudad y fecha de aplicación. Ningún
          dato publicado altera cálculos históricos.
        </div>
        <div className="cards" id="gestion">
          {sections.map(([name, detail, table]) => (
            <article key={name}>
              <p>{table}</p>
              <h2>{name}</h2>
              <span>{detail}</span>
              <strong>
                {counts[table] === null || counts[table] === undefined
                  ? 'Sin lectura'
                  : `${counts[table]} registros`}
              </strong>
            </article>
          ))}
        </div>
        <section className="activity">
          <h2>Antes de publicar</h2>
          <ul>
            <li>Verifica la fuente oficial y su URL</li>
            <li>Define fecha de vigencia y alcance territorial</li>
            <li>Conserva la versión para reproducir resultados</li>
          </ul>
        </section>
      </section>
    </main>
  );
}
