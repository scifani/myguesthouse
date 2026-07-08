const { defineConfig, devices } = require('@playwright/test');
const path = require('node:path');
const { PORT, BASE_URL, DB_PATH, ADMIN_USERNAME, ADMIN_PASSWORD } = require('./e2e/support/env');

module.exports = defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: 'list',
  globalSetup: require.resolve('./e2e/global-setup.js'),

  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],

  webServer: {
    command: 'python3 -m web.app',
    cwd: path.join(__dirname),
    url: BASE_URL,
    reuseExistingServer: false,
    timeout: 30_000,
    env: {
      DB_PATH,
      PORT,
      ADMIN_USERNAME,
      ADMIN_PASSWORD,
      SECRET_KEY: 'e2e-test-secret',
      CONFIG_FILE: path.join(__dirname, 'config.example.yaml'),
    },
  },
});
