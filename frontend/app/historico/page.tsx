import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'Histórico' };

export default function HistoricoPage() {
  return (
    <div>
      <h1>Seus planos</h1>
      {/* TODO: listagem paginada com cursor */}
    </div>
  );
}
