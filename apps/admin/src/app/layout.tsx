import './styles.css';

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <a className="skip-link" href="#contenido-principal">
          Saltar al contenido principal
        </a>
        {children}
      </body>
    </html>
  );
}
