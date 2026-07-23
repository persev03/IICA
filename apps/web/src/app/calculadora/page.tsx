'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';

const steps = ['Perfil', 'Vehículos', 'Resultado'];

export default function CalculatorPage() {
  const [step, setStep] = useState(1);

  function startEvaluation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStep(2);
  }

  function addCandidates(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStep(3);
  }

  return (
    <main className="calculator-page">
      <nav className="nav">
        <Link className="brand" href="/">
          <span className="brand-mark">I</span>IICA
        </Link>
        <span className="step-label">Perfil de compra · 1 de 3</span>
      </nav>
      <section className="calculator-shell">
        <aside>
          <p className="eyebrow">
            <span />
            Tu punto de partida
          </p>
          <h1>Cuéntanos cómo vives tu movilidad.</h1>
          <p>
            Solo pedimos lo que cambia una recomendación. Podrás completar vehículo y
            datos financieros después.
          </p>
          <ol className="steps">
            {steps.map((label, index) => (
              <li className={index + 1 === step ? 'active' : ''} key={label}>
                <span>0{index + 1}</span>
                {label}
              </li>
            ))}
          </ol>
        </aside>
        {step === 1 ? (
          <form className="profile-form" onSubmit={startEvaluation}>
            <label>
              ¿Dónde usarás principalmente el vehículo?
              <select name="city" defaultValue="bogota">
                <option value="bogota">Bogotá, Colombia</option>
                <option value="medellin">Medellín, Colombia</option>
                <option value="other">Otra ciudad</option>
              </select>
            </label>
            <label>
              ¿Cuál será su uso principal?
              <select name="use" defaultValue="mixed">
                <option value="urban">Ciudad</option>
                <option value="mixed">Mixto</option>
                <option value="road">Viajes frecuentes</option>
                <option value="family">Familia</option>
                <option value="work">Trabajo</option>
              </select>
            </label>
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
            <label className="check">
              <input type="checkbox" name="charger" /> Tengo posibilidad de instalar un
              cargador
            </label>
            <button className="button button-primary" type="submit">
              Continuar con mi perfil <span>→</span>
            </button>
          </form>
        ) : step === 2 ? (
          <form className="profile-form" onSubmit={addCandidates}>
            <p className="form-kicker">Paso 2 de 3</p>
            <h2>¿Qué vehículos tienes en mente?</h2>
            <p className="form-copy">
              Añade hasta dos versiones concretas. Próximamente podrás buscarlas en el
              catálogo validado de IICA.
            </p>
            <label>
              Primer vehículo
              <input
                name="vehicle-one"
                placeholder="Marca, modelo y versión"
                required
              />
            </label>
            <label>
              Segundo vehículo <small>(opcional)</small>
              <input name="vehicle-two" placeholder="Marca, modelo y versión" />
            </label>
            <button className="button button-primary" type="submit">
              Preparar comparación <span>→</span>
            </button>
            <button className="text-button" type="button" onClick={() => setStep(1)}>
              ← Volver al perfil
            </button>
          </form>
        ) : (
          <section className="profile-form result-pending">
            <p className="form-kicker">Paso 3 de 3</p>
            <h2>Tu comparación está preparada.</h2>
            <p className="form-copy">
              IICA calculará un único resultado explicable para cada vehículo cuando el
              motor y los datos locales estén disponibles.
            </p>
            <p className="form-notice">
              No mostramos puntuaciones preliminares: una recomendación sin datos
              vigentes no sería objetiva.
            </p>
            <button className="text-button" type="button" onClick={() => setStep(2)}>
              ← Editar vehículos
            </button>
          </section>
        )}
      </section>
    </main>
  );
}
