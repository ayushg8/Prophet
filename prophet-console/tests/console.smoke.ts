import { expect, test, type Locator, type Page } from '@playwright/test';

async function tabUntilFocused(page: Page, locator: Locator, maxTabs = 50) {
  for (let index = 0; index < maxTabs; index += 1) {
    await page.keyboard.press('Tab');
    if (await locator.evaluate((element) => element === document.activeElement)) {
      return;
    }
  }

  throw new Error(`Expected ${await locator.first().textContent()} to receive focus`);
}

test('console evidence workflow stays fixture-backed and reaches blocked', async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error' && !/favicon/i.test(message.text())) {
      consoleErrors.push(message.text());
    }
  });

  await page.goto('/');
  await page.getByRole('button', { name: /enter the operator console/i }).click();
  await expect(page.getByText(/EVALUATOR · DEMO ONLY/i)).toBeVisible();
  await expect(page.getByText(/KEV SEED · CACHED/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /refresh forecast/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /request policy-gated source refresh/i })).toHaveCount(0);
  const readinessPanel = page.getByLabel(/alpha readiness panel/i);
  await expect(readinessPanel).toBeVisible();
  await expect(readinessPanel.getByText(/Pilot policy/i)).toBeVisible();
  await expect(readinessPanel.getByText(/Safety boundary/i)).toBeVisible();
  const policyPanel = page.getByLabel(/policy status panel/i);
  await expect(policyPanel).toBeVisible();
  await expect(policyPanel.getByText(/Fixture mode/i)).toBeVisible();
  const liveCollectionGate = policyPanel.getByRole('listitem').filter({ hasText: 'Live collection workflow' });
  await expect(liveCollectionGate.getByText(/POLICY BLOCKED/i)).toBeVisible();

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

  await page.getByRole('button', { name: /load defense fixture/i }).click();
  await expect(page.getByLabel(/Defense validation status/i).getByText('BLOCKED', { exact: true })).toBeVisible();

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
  const assetContext = evidencePanel.getByLabel(/asset sbom context/i);
  await expect(assetContext.getByText(/Asset\/SBOM context/i)).toBeVisible();
  await expect(assetContext.getByText(/fixture metadata/i)).toBeVisible();
  await expect(assetContext.getByText(/3 fictional assets/i)).toBeVisible();
  await expect(assetContext.getByText(/edge_appliance/i)).toBeVisible();
  await expect(assetContext.getByText(/Edge Platform Security/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /copy evidence markdown/i })).toBeVisible();

  await page.getByRole('button', { name: /export integration handoff templates/i }).click();
  await expect(page.getByText(/Export ID/i)).toBeVisible();
  await expect(page.getByText(/review_template_only/i)).toBeVisible();
  await expect(page.getByText(/integrations\/outputs\/runtime\/latest-edge-appliance\/manifest\.json/i)).toBeVisible();
  const handoffDownloads = page.getByLabel(/handoff artifact downloads/i);
  await expect(handoffDownloads.getByText(/Review Downloads/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /download splunk handoff artifact/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /download jira handoff artifact/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /download review zip handoff artifact/i })).toBeVisible();

  await page.getByRole('button', { name: /refresh alpha readiness/i }).click();
  await expect(readinessPanel.getByText(/Evidence bundle/i)).toBeVisible();
  await expect(readinessPanel.getByText(/Integration handoff/i)).toBeVisible();

  await expect(page.getByRole('button', { name: /initiate prophet loop/i })).toBeEnabled();
  await page.getByRole('button', { name: /initiate prophet loop/i }).click();
  await expect(page.getByLabel(/Prophet loop running/i)).toBeVisible();
  await page.getByRole('button', { name: /authorize execution/i }).click({ timeout: 60_000 });
  await expect(page.getByLabel(/Defense validation status/i).getByText('BLOCKED', { exact: true })).toBeVisible({
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
  await page.getByRole('button', { name: /load defense fixture/i }).click();
  await expect(page.getByLabel(/Defense validation status/i).getByText('BLOCKED', { exact: true })).toBeVisible();

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

test('console readiness shows missing runtime outputs as non-blocking warnings', async ({ page }) => {
  await page.route('**/api/readiness', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        ok: true,
        generatedAt: '2026-05-10T00:00:00Z',
        missionId: 'readiness-warning-smoke',
        summary: {
          total: 3,
          pass: 1,
          warn: 2,
          fail: 0,
          blockingFailures: 0,
          policyId: 'prophet-pilot-fixture-localhost-v0.1',
          policySha256: '7d051922a110f024188b522b89d11782151cce2d58fa606f7c319c48f405075c',
          vmScraperEnabled: false,
          controlServer: 'localhost',
          aiMode: 'local',
          safetyBoundary: 'fixture',
        },
        checks: [
          {
            id: 'pilot_policy',
            label: 'Pilot policy',
            status: 'pass',
            details: 'Fixture policy loaded.',
            blocking: false,
          },
          {
            id: 'evidence_bundle',
            label: 'Evidence bundle',
            status: 'warn',
            details: 'Runtime evidence not generated yet; use fixture fallback.',
            blocking: false,
          },
          {
            id: 'integration_handoff',
            label: 'Integration handoff',
            status: 'warn',
            details: 'Runtime handoff manifest not generated yet; review templates are pending.',
            blocking: false,
          },
        ],
      }),
    });
  });

  await page.goto('/');
  await page.getByRole('button', { name: /enter the operator console/i }).click();

  const readinessPanel = page.getByLabel(/alpha readiness panel/i);
  const readinessSummary = readinessPanel.getByLabel(/readiness summary/i);
  await expect(readinessPanel).toBeVisible();
  await expect(readinessSummary.getByText(/READY/i)).toBeVisible();
  await expect(readinessSummary.getByText('Warn', { exact: true })).toBeVisible();
  await expect(readinessPanel.getByText(/Evidence bundle/i)).toBeVisible();
  await expect(readinessPanel.getByText(/Runtime evidence not generated yet/i)).toBeVisible();
  await expect(readinessPanel.getByText(/Integration handoff/i)).toBeVisible();
  await expect(readinessPanel.getByText(/Runtime handoff manifest not generated yet/i)).toBeVisible();
});

test('console supports keyboard navigation for the evaluator runbook path', async ({ page }) => {
  await page.goto('/');

  const enterConsole = page.getByRole('button', { name: /enter the operator console/i });
  await tabUntilFocused(page, enterConsole);
  await page.keyboard.press('Enter');
  await expect(page.getByText(/EVALUATOR · DEMO ONLY/i)).toBeVisible();

  const runbookButton = page.getByRole('button', { name: /open lab runbook/i });
  await tabUntilFocused(page, runbookButton);
  await page.keyboard.press('Enter');
  const runbookDrawer = page.locator('.runbook-drawer');
  await expect(runbookDrawer).toHaveAttribute('aria-hidden', 'false');

  const closeRunbook = page.getByRole('button', { name: /close runbook/i });
  await closeRunbook.focus();
  await page.keyboard.press('Enter');
  await expect(runbookDrawer).toHaveAttribute('aria-hidden', 'true');
});

test('console accessibility smoke keeps controls named and hidden drawers out of tab order', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /enter the operator console/i }).click();

  const unnamedControls = await page.evaluate(() =>
    Array.from(document.querySelectorAll('button, [role="button"], input, select, textarea'))
      .filter((element) => {
        const text = (element.textContent || '').replace(/\s+/g, ' ').trim();
        return !text && !element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby');
      })
      .map((element) => element.outerHTML.slice(0, 160)),
  );
  expect(unnamedControls).toEqual([]);

  const tabbableInsideHiddenRegions = await page.evaluate(() =>
    Array.from(document.querySelectorAll('[aria-hidden="true"]'))
      .flatMap((region) =>
        Array.from(
          region.querySelectorAll(
            'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]',
          ),
        ),
      )
      .filter((element) => element.getAttribute('tabindex') !== '-1')
      .map((element) => element.outerHTML.slice(0, 160)),
  );
  expect(tabbableInsideHiddenRegions).toEqual([]);

  await expect(page.getByLabel(/triage queue/i)).toBeVisible();
  await expect(page.getByLabel(/forecast brief/i)).toBeVisible();
  await expect(page.getByLabel(/defence panel/i)).toBeVisible();
  await expect(page.getByLabel(/evidence bundle panel/i)).toBeVisible();
  await expect(page.getByLabel(/integration handoff panel/i)).toBeVisible();
  await expect(page.getByLabel(/policy status panel/i)).toBeVisible();
  await expect(page.getByLabel(/alpha readiness panel/i)).toBeVisible();
});
