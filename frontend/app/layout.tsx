import type { Metadata } from 'next';
import { Fraunces, Instrument_Serif, Inter } from 'next/font/google';
import { SessionProvider } from '@/components/SessionProvider';
import '@/styles/globals.css';

const fraunces = Fraunces({
  subsets: ['latin'],
  variable: '--font-fraunces',
  display: 'swap',
  axes: ['SOFT', 'WONK'],
});

const instrumentSerif = Instrument_Serif({
  subsets: ['latin'],
  variable: '--font-instrument-serif',
  display: 'swap',
  weight: '400',
});

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  title: {
    default: 'CuradorIA — Arquiteto de Aprendizagem Holística',
    template: '%s | CuradorIA',
  },
  description:
    'Gere planos de estudo culturais e holísticos em 6 categorias: aulas, cinema, leitura, podcasts, experiências e referências.',
  metadataBase: new URL('https://curadoria.app'),
  openGraph: {
    type: 'website',
    locale: 'pt_BR',
    siteName: 'CuradorIA',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="pt-BR"
      className={`${fraunces.variable} ${instrumentSerif.variable} ${inter.variable}`}
    >
      <body>
        <SessionProvider>
          <a href="#main-content" className="skip-link">
            Ir para conteúdo principal
          </a>
          <main id="main-content">{children}</main>
        </SessionProvider>
      </body>
    </html>
  );
}
