import { test, expect, type Page } from '@playwright/test';
import { checkA11y, injectAxe } from 'axe-playwright';
import { PLANO_ID, mockPerfilVazio, mockCriarPlano } from './helpers/mock-api';

// axe-playwright depends on a different playwright-core version than @playwright/test bundles.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const castPage = (p: Page): any => p;

test.describe('Badge Descoberta (wildcard)', () => {
  test('exibe badge "Descoberta" em item is_wildcard=true', async ({ page }) => {
    await mockPerfilVazio(page);
    await mockCriarPlano(page, 0); // wildcard na categoria formal (índice 0)

    // Navigate directly to the plan page
    await page.route('**/api/v1/sessoes', async (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ session_id: 'test' }) });
      } else {
        route.continue();
      }
    });

    await page.goto(`/planos/${PLANO_ID}`);

    const badge = page.locator('[aria-label="Fator de Descoberta"]').first();
    await expect(badge).toBeVisible({ timeout: 5000 });
    await expect(badge).toContainText('Descoberta');
  });

  test('badge tem aria-label correto para acessibilidade', async ({ page }) => {
    await mockPerfilVazio(page);
    await mockCriarPlano(page, 0);

    await page.goto(`/planos/${PLANO_ID}`);

    const badge = page.locator('[aria-label="Fator de Descoberta"]').first();
    await expect(badge).toHaveAttribute('aria-label', 'Fator de Descoberta');
  });

  test('não exibe badge quando is_wildcard=false', async ({ page }) => {
    await mockPerfilVazio(page);

    // Override: no wildcards
    const makeItem = () => ({
      id: crypto.randomUUID(),
      nome: 'Item de teste',
      link: 'https://example.com',
      justificativa: 'Justificativa de teste',
      concluido: false,
      ordem: 0,
      is_wildcard: false,
    });
    const planoSemWildcard = {
      id: PLANO_ID,
      tema: 'Jazz',
      tempo_valor: 2,
      tempo_unidade: 'semanas',
      status: 'concluido',
      ia_provider: 'groq',
      categorias: (['formal', 'visual', 'leitura', 'audio', 'experiencias', 'referencias'] as const).map(
        (nome, i) => ({ id: crypto.randomUUID(), nome, ordem: i, itens: [makeItem()] })
      ),
    };

    await page.route(`**/api/v1/planos/${PLANO_ID}`, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(planoSemWildcard) })
    );

    await page.goto(`/planos/${PLANO_ID}`);

    const badge = page.locator('[aria-label="Fator de Descoberta"]');
    await expect(badge).toHaveCount(0);
  });
});

test.describe('Acessibilidade — WCAG 2.1 AA', () => {
  test('página inicial não tem violações de acessibilidade críticas', async ({ page }) => {
    await mockPerfilVazio(page);

    await page.goto('/');
    await injectAxe(castPage(page));
    await checkA11y(castPage(page), undefined, {
      axeOptions: { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] } },
      includedImpacts: ['critical', 'serious'],
    });
  });

  test('seção de personalização aberta não tem violações críticas', async ({ page }) => {
    await mockPerfilVazio(page);
    await page.goto('/');
    await page.locator('[data-testid="personalizacao-trigger"]').click();

    await injectAxe(castPage(page));
    await checkA11y(castPage(page), '[data-testid="personalizacao"]', {
      axeOptions: { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] } },
      includedImpacts: ['critical', 'serious'],
    });
  });
});
