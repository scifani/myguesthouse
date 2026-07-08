// Reusable Playwright fixtures for the admin UI. Extend `test` from here
// instead of `@playwright/test` in new specs to get an authenticated page.
const base = require('@playwright/test');
const { ADMIN_USERNAME, ADMIN_PASSWORD } = require('./env');

// Keep in sync with e2e/seed_db.py.
const FIXTURE_APARTMENT = {
  id: 'e2e-apt-1',
  name: 'E2E Appartamento',
  rossCodice: 'V00999',
};

async function login(page) {
  await page.goto('/login');
  await page.getByPlaceholder(/utente|username/i).fill(ADMIN_USERNAME);
  await page.locator('input[name="password"]').fill(ADMIN_PASSWORD);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL('**/admin');
}

async function selectApartment(page, name = FIXTURE_APARTMENT.name) {
  await page.locator('#apartmentSelect').selectOption({ label: name });
}

const test = base.test.extend({
  adminPage: async ({ page }, use) => {
    await login(page);
    await selectApartment(page);
    await use(page);
  },
});

module.exports = { test, expect: base.expect, login, selectApartment, FIXTURE_APARTMENT };
