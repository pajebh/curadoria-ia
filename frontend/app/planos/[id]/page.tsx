'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api/client';
import { SSEProgress } from '@/components/plans/SSEProgress';
import { CategoriaAccordion } from '@/components/plans/CategoriaAccordion';
import type { PlanCategory } from '@/components/plans/CategoriaAccordion';
import styles from './page.module.css';

type PlanStatus = 'pendente' | 'gerando' | 'concluido' | 'erro';
type TempoUnidade = 'dias' | 'semanas' | 'meses';

interface Plano {
  id: string;
  tema: string;
  tempo_valor: number;
  tempo_unidade: TempoUnidade;
  status: PlanStatus;
  categorias: PlanCategory[];
}

export default function PlanoPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [plano, setPlano] = useState<Plano | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPlano = useCallback(async () => {
    try {
      const data = await api.get<Plano>(`/planos/${id}`);
      setPlano(data);
    } catch {
      setError('Não foi possível carregar o plano.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void fetchPlano();
  }, [fetchPlano]);

  const handleDone = useCallback(() => {
    void fetchPlano();
  }, [fetchPlano]);

  if (loading) {
    return (
      <div className={styles.container}>
        <p>Carregando…</p>
      </div>
    );
  }

  if (error || !plano) {
    return (
      <div className={styles.container}>
        <p className={styles.erro}>
          {error ?? 'Plano não encontrado.'}{' '}
          <button onClick={() => router.push('/')}>Voltar ao início</button>
        </p>
      </div>
    );
  }

  const isGenerating = plano.status === 'pendente' || plano.status === 'gerando';

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Link href="/" className={styles.back}>← Início</Link>
        <h1 className={styles.tema}>{plano.tema}</h1>
        <p className={styles.meta}>
          {plano.tempo_valor} {plano.tempo_unidade}
        </p>
      </div>

      {isGenerating && (
        <SSEProgress planId={plano.id} onDone={handleDone} />
      )}

      {plano.status === 'erro' && (
        <p className={styles.erro}>
          Ocorreu um erro na geração.{' '}
          <button onClick={() => router.push('/')}>Tentar novamente</button>
        </p>
      )}

      {plano.status === 'concluido' && plano.categorias.length > 0 && (
        <CategoriaAccordion planId={plano.id} categorias={plano.categorias} />
      )}
    </div>
  );
}
