'use client';

import { useEffect, useState } from 'react';

const API_PREFIX = '/api/v1';

export type StreamStage = 'moderacao' | 'gerando' | 'validando' | 'done' | 'erro';

export interface PlanStreamState {
  progress: number;
  stage: StreamStage | undefined;
  done: boolean;
  error: string | undefined;
}

export function usePlanStream(planId: string | null): PlanStreamState {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState<StreamStage | undefined>(undefined);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (!planId) return;

    const es = new EventSource(`${API_PREFIX}/planos/${planId}/stream`, {
      withCredentials: true,
    });

    es.addEventListener('progress', (e: MessageEvent<string>) => {
      try {
        const data = JSON.parse(e.data) as { percent: number; stage: StreamStage };
        setProgress(data.percent);
        setStage(data.stage);
      } catch {
        // ignora parse errors
      }
    });

    es.addEventListener('done', () => {
      setProgress(100);
      setStage('done');
      setDone(true);
      es.close();
    });

    es.addEventListener('erro', (e: MessageEvent<string>) => {
      try {
        const data = JSON.parse(e.data) as { message: string };
        setError(data.message);
      } catch {
        setError('Erro na geração do plano');
      }
      setStage('erro');
      setDone(true);
      es.close();
    });

    es.onerror = () => {
      // Fecha a conexão se houver erro de rede
      // O componente pode fazer polling como fallback
      es.close();
    };

    return () => {
      es.close();
    };
  }, [planId]);

  return { progress, stage, done, error };
}
