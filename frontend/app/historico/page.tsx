'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/client';
import { Button } from '@/components/ui/Button';
import styles from './page.module.css';

type PlanStatus = 'pendente' | 'gerando' | 'concluido' | 'erro';

interface PlanoResumo {
  id: string;
  tema: string;
  tempo_valor: number;
  tempo_unidade: string;
  status: PlanStatus;
  criado_em: string | null;
}

interface PlanosList {
  items: PlanoResumo[];
  next_cursor: string | null;
}

const STATUS_LABELS: Record<PlanStatus, string> = {
  pendente: 'Gerando',
  gerando: 'Gerando',
  concluido: 'Concluído',
  erro: 'Erro',
};

function formatData(iso: string | null) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' });
}

export default function HistoricoPage() {
  const [planos, setPlanos] = useState<PlanoResumo[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  async function fetchPlanos(nextCursor?: string) {
    const path = nextCursor
      ? `/sessoes/me/planos?cursor=${nextCursor}`
      : '/sessoes/me/planos';
    const data = await api.get<PlanosList>(path);
    return data;
  }

  useEffect(() => {
    setLoading(true);
    fetchPlanos()
      .then(data => {
        setPlanos(data.items);
        setCursor(data.next_cursor);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function loadMore() {
    if (!cursor) return;
    setLoadingMore(true);
    try {
      const data = await fetchPlanos(cursor);
      setPlanos(prev => [...prev, ...data.items]);
      setCursor(data.next_cursor);
    } finally {
      setLoadingMore(false);
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Link href="/" className={styles.back}>← Início</Link>
        <h1 className={styles.title}>Seus planos</h1>
      </div>

      {loading ? (
        <p className={styles.empty}>Carregando…</p>
      ) : planos.length === 0 ? (
        <p className={styles.empty}>
          Nenhum plano ainda.{' '}
          <Link href="/" className={styles.link}>Crie o primeiro!</Link>
        </p>
      ) : (
        <>
          <ul className={styles.list}>
            {planos.map(p => (
              <li key={p.id}>
                <Link href={`/planos/${p.id}`} className={styles.card}>
                  <div className={styles.cardMain}>
                    <span className={styles.tema}>{p.tema}</span>
                    <span className={`${styles.status} ${styles[p.status]}`}>
                      {STATUS_LABELS[p.status]}
                    </span>
                  </div>
                  <div className={styles.cardMeta}>
                    <span>{p.tempo_valor} {p.tempo_unidade}</span>
                    {p.criado_em && <span>{formatData(p.criado_em)}</span>}
                  </div>
                </Link>
              </li>
            ))}
          </ul>

          {cursor && (
            <div className={styles.more}>
              <Button onClick={loadMore} loading={loadingMore} size="sm">
                Carregar mais
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
