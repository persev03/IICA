'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';

const steps = ['Uso', 'Presupuesto', 'Ubicación'];

export default function CalculatorPage() {
  const [submitted, setSubmitted] = useState(false);

  function startEvaluation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitted(true);
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
            {steps.map((step, index) => (
              <li className={index === 0 ? 'active' : ''} key={step}>
                <span>0{index + 1}</span>
                {step}
              </li>
            ))}
          </ol>
        </aside>
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
          {submitted && (
            <p className="form-notice">
              Perfil guardado en esta sesión. El siguiente paso será elegir los
              vehículos a comparar.
            </p>
          )}
        </form>
      </section>
    </main>
  );
}
