import type { Metadata } from 'next';
import './styles.css';

export const metadata: Metadata = {
  title: 'IICA | El automóvil indicado para ti',
  description:
    'Índice Inteligente de Compra de Automóviles: una decisión personalizada, objetiva y explicable.',
};

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
