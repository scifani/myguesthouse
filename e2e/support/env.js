// Shared env/config used by both playwright.config.js (to launch the Flask
// webServer) and global-setup.js (to seed its database before tests run).
const path = require('node:path');
const os = require('node:os');

const PORT = process.env.E2E_PORT || '5057';
const DB_PATH = path.join(os.tmpdir(), 'myguesthouse-e2e.db');
const ADMIN_USERNAME = 'e2e-admin';
const ADMIN_PASSWORD = 'e2e-test-password';

module.exports = {
  PORT,
  BASE_URL: `http://127.0.0.1:${PORT}`,
  DB_PATH,
  ADMIN_USERNAME,
  ADMIN_PASSWORD,
};
