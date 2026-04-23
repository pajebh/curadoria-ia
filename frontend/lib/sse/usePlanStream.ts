'use client';

import { useEffect, useState } from 'react';

const API_PREFIX = '/api/v1';

export type StreamStage = 'moderacao' | 'gerando' | 'validando' | 'done' | 'erro';

export interface LinkCheckUpdate {
  item_id: string;
  status: 'valid' | 'repaired' | 'broken';
  link?: string;
}

export interface PlanStreamState {
  progress: number;
  stage: StreamStage | undefined;
  done: boolean;
  complete: boolean;
  error: string | undefined;
  linkUpdates: LinkCheckUpdate[];
}

export function usePlanStream(planId: string | null): PlanStreamState {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState<StreamStage | undefined>(undefined);
  const [done, setDone] = useState(false);
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [linkUpdates, setLinkUpdates] = useState<LinkCheckUpdate[]>([]);

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
      // stream stays open for link_check events — closed by 'complete'
    });

    es.addEventListener('link_check', (e: MessageEvent<string>) => {
      try {
        const data = JSON.parse(e.data) as LinkCheckUpdate;
        setLinkUpdates(prev => [...prev, data]);
      } catch {
        // ignora parse errors
      }
    });

    es.addEventListener('complete', () => {
      setComplete(true);
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
      setComplete(true);
      es.close();
    });

    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
    };
  }, [planId]);

  return { progress, stage, done, complete, error, linkUpdates };
}
