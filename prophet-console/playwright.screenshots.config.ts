import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: /.*\.screenshots\.ts/,
  timeout: 120_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: 'http://127.0.0.1:53173',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command:
        'PROPHET_CONTROL_PORT=58787 PROPHET_OPERATOR_AUDIT_LOG=evidence/outputs/runtime/browser-screenshot-operator-audit-log.jsonl PROPHET_APPROVAL_RECORD_JSON=evidence/outputs/runtime/browser-screenshot-approval-record.json npm run dev:control',
      url: 'http://127.0.0.1:58787/health',
      reuseExistingServer: false,
      timeout: 20_000,
    },
    {
      command:
        'VITE_PROPHET_CONTROL_ORIGIN=http://127.0.0.1:58787 VITE_PROPHET_EVALUATOR_MODE=1 npm run dev -- --host 127.0.0.1 --port 53173 --strictPort',
      url: 'http://127.0.0.1:53173',
      reuseExistingServer: false,
      timeout: 20_000,
    },
  ],
});
