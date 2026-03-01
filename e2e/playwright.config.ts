import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: 'http://localhost:5000',
    viewport: { width: 480, height: 480 }, // HyperPixel round display
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'cd ../backend && python3 app.py',
    url: 'http://localhost:5000/api/health',
    reuseExistingServer: true,
    timeout: 10000,
    env: {
      FLASK_DEBUG: '1',
    },
  },
});
