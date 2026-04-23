import type { Page, Route } from '@playwright/test';

export const PLANO_ID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

export async function mockPerfilVazio(page: Page): Promise<void> {
  await page.route('**/api/v1/sessoes/perfil', (route: Route) => {
    if (route.request().method() === 'GET') {
      route.fulfill({ status: 204 });
    } else {
      route.continue();
    }
  });
}

export async function mockPerfilExistente(page: Page): Promise<void> {
  const perfil = {
    nivel: 'intermediario',
    orcamento: 'gratuito',
    idioma: 'apenas_portugues',
    rotina: 'prefere_ler',
    motivacao: 'curiosidade',
    atualizado_em: '2026-04-23T12:00:00',
  };
  await page.route('**/api/v1/sessoes/perfil', (route: Route) => {
    if (route.request().method() === 'GET') {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(perfil) });
    } else if (route.request().method() === 'PUT') {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(perfil) });
    } else {
      route.continue();
    }
  });
}

export async function mockCriarPlano(page: Page, wildcardCatIndex = 0): Promise<void> {
  const makeItem = (isWildcard = false) => ({
    id: crypto.randomUUID(),
    nome: 'Item de teste',
    link: 'https://example.com',
    justificativa: 'Justificativa de teste',
    concluido: false,
    ordem: 0,
    is_wildcard: isWildcard,
  });

  const planoData = {
    id: PLANO_ID,
    tema: 'Jazz',
    tempo_valor: 2,
    tempo_unidade: 'semanas',
    status: 'concluido',
    ia_provider: 'groq',
    categorias: [
      { id: crypto.randomUUID(), nome: 'formal', ordem: 0, itens: [makeItem(wildcardCatIndex === 0)] },
      { id: crypto.randomUUID(), nome: 'visual', ordem: 1, itens: [makeItem(wildcardCatIndex === 1)] },
      { id: crypto.randomUUID(), nome: 'leitura', ordem: 2, itens: [makeItem()] },
      { id: crypto.randomUUID(), nome: 'audio', ordem: 3, itens: [makeItem()] },
      { id: crypto.randomUUID(), nome: 'experiencias', ordem: 4, itens: [makeItem()] },
      { id: crypto.randomUUID(), nome: 'referencias', ordem: 5, itens: [makeItem()] },
    ],
  };

  // POST /planos → 202 Accepted
  await page.route('**/api/v1/planos', (route: Route) => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({ plano_id: PLANO_ID, stream_url: `/v1/planos/${PLANO_ID}/stream` }),
      });
    } else {
      route.continue();
    }
  });

  // GET /planos/{id} → plano completo
  await page.route(`**/api/v1/planos/${PLANO_ID}`, (route: Route) => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(planoData) });
  });

  // SSE stream → immediately closes (done event)
  await page.route(`**/api/v1/planos/${PLANO_ID}/stream`, (route: Route) => {
    route.fulfill({
      status: 200,
      contentType: 'text/event-stream',
      body: 'data: {"event":"done","percent":100}\n\n',
    });
  });
}
