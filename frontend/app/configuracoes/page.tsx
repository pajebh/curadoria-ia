import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'Configurações' };

export default function ConfiguracoesPage() {
  return (
    <div>
      <h1>Configurações</h1>
      {/* TODO: botão apagar dados (LGPD) + exportar */}
    </div>
  );
}
