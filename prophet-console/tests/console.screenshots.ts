import { expect, test, type Page } from '@playwright/test';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const screenshotDir = path.resolve(process.cwd(), '../evidence/outputs/runtime/console-screenshots');

const viewports = [
  { id: 'desktop', width: 1440, height: 1000 },
  { id: 'mobile', width: 390, height: 844 },
];

type ScreenshotArtifact = {
  id: string;
  path: string;
  sha256: string;
  viewport: {
    width: number;
    height: number;
  };
};

test('captures redacted responsive evaluator screenshots', async ({ page }) => {
  await mkdir(screenshotDir, { recursive: true });
  const artifacts: ScreenshotArtifact[] = [];

  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto('/');
    await page.getByRole('button', { name: /enter the operator console/i }).click();
    await expect(page.getByText(/EVALUATOR · DEMO ONLY/i)).toBeVisible();
    await expect(page.getByText('FIXTURE MODE · ACTIVE', { exact: true })).toBeVisible();
    await capture(page, viewport, 'entry', artifacts);

    await page.getByRole('button', { name: /refresh forecast/i }).click();
    await expect(page.getByText(/Demo forecast refreshed/i)).toBeVisible();
    await capture(page, viewport, 'forecast', artifacts);

    await page.getByRole('button', { name: /load defense fixture/i }).click();
    await expect(page.getByLabel(/Defense validation status/i).getByText('BLOCKED', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: /generate evidence bundle/i }).click();
    await expect(page.getByText(/Bundle SHA-256/i)).toBeVisible();
    await page.getByRole('button', { name: /export integration handoff templates/i }).click();
    await expect(page.getByText(/review_template_only/i)).toBeVisible();
    await capture(page, viewport, 'evidence-handoff', artifacts);

    await assertNoUnsafeScreenshotText(page);
  }

  await writeFile(
    path.join(screenshotDir, 'manifest.json'),
    JSON.stringify(
      {
        schema_version: 'prophet_console_screenshot_manifest.v0.1',
        generated_by: 'npm run capture:screenshots',
        output_dir: 'evidence/outputs/runtime/console-screenshots',
        data_boundary: {
          fixture_backed: true,
          browser_chrome_excluded: true,
          no_customer_systems: true,
          no_live_targets: true,
          no_payloads: true,
          no_credentials: true,
          review_required_before_sharing: true,
        },
        artifacts,
      },
      null,
      2,
    ) + '\n',
    'utf-8',
  );
});

async function capture(
  page: Page,
  viewport: { id: string; width: number; height: number },
  state: string,
  artifacts: ScreenshotArtifact[],
) {
  const filename = `console-${viewport.id}-${state}.png`;
  const outputPath = path.join(screenshotDir, filename);
  if (viewport.id === 'mobile' && state === 'evidence-handoff') {
    await page.locator('.evidence-panel').scrollIntoViewIfNeeded();
  } else if (viewport.id === 'mobile') {
    await page.locator('.header-wrapper').scrollIntoViewIfNeeded();
  } else {
    await page.evaluate(() => window.scrollTo(0, 0));
  }
  await page.screenshot({ path: outputPath });
  const bytes = await readFile(outputPath);
  artifacts.push({
    id: `console-${viewport.id}-${state}`,
    path: `evidence/outputs/runtime/console-screenshots/${filename}`,
    sha256: createHash('sha256').update(bytes).digest('hex'),
    viewport: {
      width: viewport.width,
      height: viewport.height,
    },
  });
}

async function assertNoUnsafeScreenshotText(page: Page) {
  const bodyText = await page.locator('body').innerText();
  expect(bodyText).not.toMatch(/\b\d{1,3}(?:\.\d{1,3}){3}\b/);
  expect(bodyText).not.toMatch(/\$\{jndi:/i);
  expect(bodyText).not.toMatch(/BEGIN (RSA|OPENSSH|PRIVATE) KEY/i);
  expect(bodyText).not.toMatch(/\b(ssh-rsa|ssh-ed25519)\b/i);
  expect(bodyText).not.toMatch(/\b(password|secret|token)\s*[:=]/i);
  expect(bodyText).not.toMatch(/auto-?deploy/i);
}
