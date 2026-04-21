import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'Plano' };

interface Props {
  params: Promise<{ id: string }>;
}

export default async function PlanoPage({ params }: Props) {
  const { id } = await params;

  return (
    <div>
      <p>Plano {id} — em desenvolvimento.</p>
      {/* TODO: CategoriaAccordion, SSEProgress, progresso */}
    </div>
  );
}
