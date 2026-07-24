import Link from 'next/link';

const sections = [
  ['Catálogo', 'Marcas, modelos y versiones', 'vehicle_brands'],
  ['Territorio', 'Países, departamentos y ciudades', 'countries'],
  ['Reglas locales', 'Impuestos, incentivos y movilidad', 'tax_rules'],
  ['Infraestructura', 'Carga, talleres y concesionarios', 'infrastructure_snapshots'],
];

export default function AdminHome() {
  return (
    <main className="admin">
      <aside>
        <Link className="admin-brand" href="/">
          IICA <span>Admin</span>
        </Link>
        <nav>
          {sections.map(([name]) => (
            <a href="#gestion" key={name}>
              {name}
            </a>
          ))}
        </nav>
        <small>Protegido por sesión administrativa</small>
      </aside>
      <section id="contenido-principal" tabIndex={-1}>
        <header>
          <div>
            <p>Administración</p>
            <h1>Datos que sostienen cada IICA.</h1>
          </div>
          <button>+ Nuevo registro</button>
        </header>
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
              <a href="#gestion" aria-label={`Gestionar ${name}`}>
                Gestionar →
              </a>
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
