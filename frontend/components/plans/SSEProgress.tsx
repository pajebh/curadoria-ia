'use client';

import * as Progress from '@radix-ui/react-progress';
import { useEffect, useRef } from 'react';
import { usePlanStream } from '@/lib/sse/usePlanStream';
import type { LinkCheckUpdate, StreamStage } from '@/lib/sse/usePlanStream';
import styles from './SSEProgress.module.css';

const STAGE_LABELS: Record<StreamStage, string> = {
  moderacao: 'Analisando tema…',
  gerando: 'Gerando seu plano com IA…',
  validando: 'Validando conteúdo…',
  done: 'Verificando links…',
  erro: 'Ocorreu um erro',
};

interface SSEProgressProps {
  planId: string;
  onDone: () => void;
  onLinkUpdate?: (update: LinkCheckUpdate) => void;
}

export function SSEProgress({ planId, onDone, onLinkUpdate }: SSEProgressProps) {
  const { progress, stage, done, complete, error, linkUpdates } = usePlanStream(planId);
  const doneFiredRef = useRef(false);
  const processedRef = useRef(0);

  useEffect(() => {
    if (done && !error && !doneFiredRef.current) {
      doneFiredRef.current = true;
      onDone();
    }
  }, [done, error, onDone]);

  useEffect(() => {
    if (!onLinkUpdate) return;
    const newUpdates = linkUpdates.slice(processedRef.current);
    newUpdates.forEach(u => onLinkUpdate(u));
    processedRef.current = linkUpdates.length;
  }, [linkUpdates, onLinkUpdate]);

  if (complete && !error) return null;

  return (
    <div className={styles.container} aria-live="polite" aria-label="Progresso da geração do plano">
      <p className={styles.stage}>
        {stage ? STAGE_LABELS[stage] : 'Iniciando…'}
      </p>

      <Progress.Root
        className={styles.progressRoot}
        value={progress}
        aria-label={`${progress}% concluído`}
      >
        <Progress.Indicator
          className={styles.progressIndicator}
          style={{ width: `${progress}%` }}
        />
      </Progress.Root>

      <p className={styles.percent}>{progress}%</p>

      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
