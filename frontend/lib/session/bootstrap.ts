import { api } from '@/lib/api/client';

export async function ensureSession(): Promise<void> {
  // O middleware Next.js já garante a criação da sessão via cookie.
  // Este helper é para casos onde o cookie pode ter expirado client-side.
  try {
    await api.post('/sessoes', {});
  } catch {
    // Sessão já existe ou backend temporariamente indisponível — ok
  }
}
