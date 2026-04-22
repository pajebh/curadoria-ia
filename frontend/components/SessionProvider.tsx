'use client';

import { useEffect } from 'react';
import { api } from '@/lib/api/client';

export function SessionProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    api.post('/sessoes', {}).catch(() => {});
  }, []);

  return <>{children}</>;
}
