import { expect, test } from '@playwright/test';

test('console evidence workflow stays fixture-backed and reaches blocked', async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error' && !/favicon/i.test(message.text())) {
      consoleErrors.push(message.text());
    }
  });

  await page.goto('/');
  await page.getByRole('button', { name: /enter the operator console/i }).click();
  await expect(page.getByRole('button', { name: /refresh forecast/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /run isolated scraper vm workflow/i })).toHaveCount(0);
  const readinessPanel = page.getByLabel(/alpha readiness panel/i);
  await expect(readinessPanel).toBeVisible();
  await expect(readinessPanel.getByText(/Pilot policy/i)).toBeVisible();
  await expect(readinessPanel.getByText(/Safety boundary/i)).toBeVisible();
  const policyPanel = page.getByLabel(/policy status panel/i);
  await expect(policyPanel).toBeVisible();
  await expect(policyPanel.getByText(/Fixture mode/i)).toBeVisible();
  const liveVmGate = policyPanel.getByRole('listitem').filter({ hasText: 'Live VM scraper' });
  await expect(liveVmGate.getByText(/POLICY BLOCKED/i)).toBeVisible();

  await page.route('**/api/scraper/demo-refresh', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        ok: false,
        status: 'policy_blocked',
        message: 'Pilot policy blocks seeded OSINT refresh.',
      }),
    });
  });
  await page.getByRole('button', { name: /refresh forecast/i }).click();
  await expect(
    page.getByText(/Policy blocked: Pilot policy blocks seeded OSINT refresh/i),
  ).toBeVisible();
  await page.unroute('**/api/scraper/demo-refresh');

  await page.getByRole('button', { name: /refresh forecast/i }).click();
  await expect(page.getByText(/Demo forecast refreshed/i)).toBeVisible();

  await page.getByRole('button', { name: /load cyber defense fixture/i }).click();
  await expect(page.getByLabel(/Exploit status/i).getByText('BLOCKED', { exact: true })).toBeVisible();

  await page.getByRole('button', { name: /generate evidence bundle/i }).click();
  const evidencePanel = page.getByLabel(/evidence bundle panel/i);
  await expect(page.getByText(/Bundle ID/i)).toBeVisible();
  await expect(page.getByText(/Bundle SHA-256/i)).toBeVisible();
  const artifactSource = evidencePanel.getByLabel(/sandbox artifact source/i);
  await expect(artifactSource.getByText(/Artifact source/i)).toBeVisible();
  await expect(artifactSource.getByText(/Sandbox runtime artifact|Checked-in defense fixture/i)).toBeVisible();
  const sourceHealth = evidencePanel.getByLabel(/source freshness and failures/i);
  await expect(sourceHealth.getByText(/OSINT basis/i)).toBeVisible();
  await expect(sourceHealth.getByText(/current \/ ok/i)).toBeVisible();
  await expect(sourceHealth.getByText(/Newest age/i)).toBeVisible();
  await expect(sourceHealth.getByText(/No sanitized source failures recorded/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /copy evidence markdown/i })).toBeVisible();

  await page.getByRole('button', { name: /export integration handoff templates/i }).click();
  await expect(page.getByText(/Export ID/i)).toBeVisible();
  await expect(page.getByText(/review_template_only/i)).toBeVisible();
  await expect(page.getByText(/integrations\/outputs\/runtime\/latest-edge-appliance\/manifest\.json/i)).toBeVisible();

  await page.getByRole('button', { name: /refresh alpha readiness/i }).click();
  await expect(readinessPanel.getByText(/Evidence bundle/i)).toBeVisible();
  await expect(readinessPanel.getByText(/Integration handoff/i)).toBeVisible();

  await expect(page.getByRole('button', { name: /initiate prophet loop/i })).toBeEnabled();
  await page.getByRole('button', { name: /initiate prophet loop/i }).click();
  await expect(page.getByLabel(/Prophet loop running/i)).toBeVisible();
  await page.getByRole('button', { name: /authorize execution/i }).click({ timeout: 60_000 });
  await expect(page.getByLabel(/Exploit status/i).getByText('BLOCKED', { exact: true })).toBeVisible({
    timeout: 45_000,
  });
  await expect(page.getByRole('button', { name: /initiate prophet loop/i })).toBeVisible({
    timeout: 20_000,
  });

  expect(consoleErrors).toEqual([]);
});

test('console evidence panel shows sanitized source failures', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /enter the operator console/i }).click();
  await page.getByRole('button', { name: /load cyber defense fixture/i }).click();
  await expect(page.getByLabel(/Exploit status/i).getByText('BLOCKED', { exact: true })).toBeVisible();

  await page.route('**/api/evidence/demo-bundle', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        ok: true,
        status: 'evidence_bundle_generated',
        artifactSource: 'checked_in_fixture',
        artifactSourceLabel: 'checked-in defense fixture',
        artifactMode: 'fixture',
        paths: {
          defenseArtifact: 'cyber-side/fixtures/exploit-engine-output-edge-appliance.json',
        },
        markdown: '# Mock Evidence',
        bundle: {
          bundle_id: 'mock-source-failure-bundle',
          bundle_sha256: 'f'.repeat(64),
          input_refs: {
            forecast_id: 'mock-forecast',
            artifact_id: 'mock-artifact',
          },
          operator_approval: {
            decision: 'bypassed_for_fixture',
          },
          validation_summary: {
            post_patch_status: 'blocked',
          },
          open_source_summary: {
            integrated: true,
            freshness: {
              status: 'stale',
              newest_record_observed_at: '2026-04-01T00:00:00Z',
              newest_record_age_days: 33.5,
              freshness_window_days: 7,
            },
            source_health: {
              status: 'degraded',
              successful_source_count: 2,
              failed_source_count: 1,
            },
            source_failures: [
              {
                source_id: 'osv_query_api_seed',
                status: 'failed',
                error: 'fixture timeout',
              },
            ],
          },
        },
      }),
    });
  });

  await page.getByRole('button', { name: /generate evidence bundle/i }).click();
  const sourceHealth = page.getByLabel(/source freshness and failures/i);
  await expect(sourceHealth.getByText(/stale \/ degraded/i)).toBeVisible();
  await expect(sourceHealth.getByText(/osv_query_api_seed/i)).toBeVisible();
  await expect(sourceHealth.getByText(/fixture timeout/i)).toBeVisible();
});
