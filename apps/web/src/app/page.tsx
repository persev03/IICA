const signals = [
  ['01', 'Tu realidad', 'Presupuesto, familia, uso, viajes y horizonte de propiedad.'],
  ['02', 'Tu ciudad', 'Impuestos, movilidad, incentivos e infraestructura local.'],
  ['03', 'El vehículo', 'Costos, seguridad, autonomía, reventa y experiencia real.'],
];

export default function Home() {
  return (
    <main id="contenido-principal" tabIndex={-1}>
      <nav className="nav" aria-label="Navegación principal">
        <a className="brand" href="#inicio" aria-label="IICA inicio">
          <span className="brand-mark">I</span>IICA
        </a>
        <div className="nav-links">
          <a href="#metodo">Metodología</a>
          <a href="#indice">El índice</a>
          <a className="nav-action" href="#calcular">
            Calcular mi IICA
          </a>
        </div>
      </nav>

      <section className="hero" id="inicio">
        <div className="hero-copy">
          <p className="eyebrow">
            <span />
            Decisiones que sí te corresponden
          </p>
          <h1>
            No buscamos el mejor automóvil.
            <br />
            <em>Encontramos el mejor para ti.</em>
          </h1>
          <p className="hero-description">
            IICA transforma tu perfil, tu ciudad y cada vehículo en una recomendación
            única, objetiva y fácil de entender.
          </p>
          <div className="hero-actions" id="calcular">
            <a className="button button-primary" href="/calculadora">
              Calcular mi IICA <span aria-hidden="true">↗</span>
            </a>
            <a className="button button-quiet" href="#metodo">
              Conocer la metodología <span aria-hidden="true">↓</span>
            </a>
          </div>
          <p className="disclaimer">
            Próximamente · Construido para decisiones reales, no para rankings.
          </p>
        </div>

        <div
          className="index-card"
          aria-label="Ejemplo ilustrativo de una puntuación IICA"
        >
          <div className="card-top">
            <span>Resultado personalizado</span>
            <span className="live-dot">En contexto</span>
          </div>
          <div className="score-row">
            <div>
              <span className="score">91</span>
              <span className="out-of">/100</span>
            </div>
            <div className="badge">
              Excelente
              <br />
              compra
            </div>
          </div>
          <div className="score-line">
            <span />
          </div>
          <div className="card-insight">
            <span className="spark">✦</span>
            <p>
              Equilibrio destacado entre costo total, autonomía y restricciones en tu
              ciudad.
            </p>
          </div>
          <p className="card-caption">
            Ejemplo de resultado — no es una recomendación de compra.
          </p>
        </div>
      </section>

      <section className="proof" id="metodo">
        <p>Una buena compra no es una ficha técnica. Es una decisión completa.</p>
        <div className="signal-grid">
          {signals.map(([number, title, detail]) => (
            <article className="signal" key={number}>
              <span>{number}</span>
              <h2>{title}</h2>
              <p>{detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="method" id="indice">
        <p className="eyebrow">
          <span />
          Un solo índice. Explicado.
        </p>
        <div className="method-grid">
          <h2>Una puntuación que puedes defender.</h2>
          <p>
            IICA reúne las variables relevantes en un resultado de 0 a 100 y te muestra
            qué inclinó la balanza. Sin recomendaciones opacas. Sin reducir tu vida a
            una lista de especificaciones.
          </p>
        </div>
      </section>

      <footer>
        <span>© 2026 IICA</span>
        <span>Índice Inteligente de Compra de Automóviles</span>
      </footer>
    </main>
  );
}
