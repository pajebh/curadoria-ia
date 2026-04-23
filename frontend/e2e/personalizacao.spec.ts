import { test, expect } from '@playwright/test';
import { mockPerfilVazio, mockPerfilExistente, mockCriarPlano } from './helpers/mock-api';

test.describe('Personalização do Plano — seção colapsável', () => {
  test.beforeEach(async ({ page }) => {
    await mockPerfilVazio(page);
    await mockCriarPlano(page);
  });

  test('seção está fechada por padrão na primeira visita', async ({ page }) => {
    await page.goto('/');
    const details = page.locator('details[data-testid="personalizacao"]');
    await expect(details).not.toHaveAttribute('open');
  });

  test('abre e fecha ao clicar no summary', async ({ page }) => {
    await page.goto('/');
    const summary = page.locator('[data-testid="personalizacao-trigger"]');
    await summary.click();
    const details = page.locator('details[data-testid="personalizacao"]');
    await expect(details).toHaveAttribute('open', '');

    await summary.click();
    await expect(details).not.toHaveAttribute('open');
  });

  test('todos os campos estão presentes na seção aberta', async ({ page }) => {
    await page.goto('/');
    await page.locator('[data-testid="personalizacao-trigger"]').click();

    await expect(page.locator('#ctx-nivel')).toBeVisible();
    await expect(page.locator('#ctx-orcamento')).toBeVisible();
    await expect(page.locator('#ctx-idioma')).toBeVisible();
    await expect(page.locator('#ctx-rotina')).toBeVisible();
    await expect(page.locator('#ctx-localizacao')).toBeVisible();
    await expect(page.locator('#ctx-motivacao')).toBeVisible();
  });

  test('touch targets dos selects têm altura ≥ 44px', async ({ page }) => {
    await page.goto('/');
    await page.locator('[data-testid="personalizacao-trigger"]').click();

    for (const id of ['ctx-nivel', 'ctx-orcamento', 'ctx-idioma', 'ctx-rotina', 'ctx-motivacao']) {
      const el = page.locator(`#${id}`);
      const box = await el.boundingBox();
      expect(box?.height).toBeGreaterThanOrEqual(44);
    }
  });
});

test.describe('Personalização do Plano — pré-preenchimento com perfil salvo', () => {
  test.beforeEach(async ({ page }) => {
    await mockPerfilExistente(page);
    await mockCriarPlano(page);
  });

  test('seção abre automaticamente quando perfil existe', async ({ page }) => {
    await page.goto('/');
    const details = page.locator('details[data-testid="personalizacao"]');
    await expect(details).toHaveAttribute('open', '', { timeout: 5000 });
  });

  test('campos pré-preenchidos com valores do perfil salvo', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#ctx-nivel')).toHaveValue('intermediario', { timeout: 5000 });
    await expect(page.locator('#ctx-orcamento')).toHaveValue('gratuito');
    await expect(page.locator('#ctx-idioma')).toHaveValue('apenas_portugues');
    await expect(page.locator('#ctx-rotina')).toHaveValue('prefere_ler');
    await expect(page.locator('#ctx-motivacao')).toHaveValue('curiosidade');
  });

  test('localização não é pré-preenchida (não persiste)', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#ctx-localizacao')).toHaveValue('');
  });
});

test.describe('Personalização do Plano — submit', () => {
  test('envia plano sem contexto quando campos vazios (backward compat)', async ({ page }) => {
    await mockPerfilVazio(page);

    const requests: string[] = [];
    await page.route('**/api/v1/planos', async (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON();
        requests.push(JSON.stringify(body));
        await route.fulfill({
          status: 202,
          contentType: 'application/json',
          body: JSON.stringify({ plano_id: 'test-id', stream_url: '/v1/planos/test-id/stream' }),
        });
      } else {
        await route.continue();
      }
    });
    await page.route('**/api/v1/planos/test-id/stream', (route) =>
      route.fulfill({ status: 200, contentType: 'text/event-stream', body: 'data: {"event":"done","percent":100}\n\n' })
    );
    await page.route('**/api/v1/planos/test-id', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        id: 'test-id', tema: 'Jazz', tempo_valor: 2, tempo_unidade: 'semanas',
        status: 'concluido', categorias: []
      }) })
    );

    await page.goto('/');
    await page.fill('[name="tema"]', 'Jazz');
    await page.locator('[name="tempo_valor"]').fill('2');
    await page.locator('button[type="submit"]').click();

    await expect(page).toHaveURL(/\/planos\/test-id/, { timeout: 10000 });

    const body = JSON.parse(requests[0] ?? '{}');
    expect(body.contexto).toBeUndefined();
  });

  test('envia contexto no body quando campos preenchidos', async ({ page }) => {
    await mockPerfilVazio(page);

    const requests: string[] = [];
    await page.route('**/api/v1/planos', async (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON();
        requests.push(JSON.stringify(body));
        await route.fulfill({
          status: 202,
          contentType: 'application/json',
          body: JSON.stringify({ plano_id: 'ctx-id', stream_url: '/v1/planos/ctx-id/stream' }),
        });
      } else {
        await route.continue();
      }
    });
    await page.route('**/api/v1/planos/ctx-id/stream', (route) =>
      route.fulfill({ status: 200, contentType: 'text/event-stream', body: 'data: {"event":"done","percent":100}\n\n' })
    );
    await page.route('**/api/v1/planos/ctx-id', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        id: 'ctx-id', tema: 'Jazz', tempo_valor: 2, tempo_unidade: 'semanas',
        status: 'concluido', categorias: []
      }) })
    );
    await page.route('**/api/v1/sessoes/perfil', (route) =>
      route.request().method() === 'GET'
        ? route.fulfill({ status: 204 })
        : route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    );

    await page.goto('/');
    await page.fill('[name="tema"]', 'Jazz');
    await page.locator('[name="tempo_valor"]').fill('2');
    await page.locator('[data-testid="personalizacao-trigger"]').click();

    await page.selectOption('#ctx-nivel', 'basico');
    await page.selectOption('#ctx-orcamento', 'gratuito');
    await page.fill('#ctx-localizacao', 'Recife, PE');

    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/\/planos\/ctx-id/, { timeout: 10000 });

    const body = JSON.parse(requests[0] ?? '{}');
    expect(body.contexto).toBeDefined();
    expect(body.contexto.nivel).toBe('basico');
    expect(body.contexto.orcamento).toBe('gratuito');
    expect(body.contexto.localizacao).toBe('Recife, PE');
  });
});
