'use client';

import * as Progress from '@radix-ui/react-progress';
import { usePlanStream } from '@/lib/sse/usePlanStream';
import type { StreamStage } from '@/lib/sse/usePlanStream';
import styles from './SSEProgress.module.css';

const STAGE_LABELS: Record<StreamStage, string> = {
  moderacao: 'Analisando tema…',
  gerando: 'Gerando seu plano com IA…',
  validando: 'Validando conteúdo…',
  done: 'Plano gerado!',
  erro: 'Ocorreu um erro',
};

interface SSEProgressProps {
  planId: string;
  onDone: () => void;
}

export function SSEProgress({ planId, onDone }: SSEProgressProps) {
  const { progress, stage, done, error } = usePlanStream(planId);

  if (done && !error) {
    onDone();
  }

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
