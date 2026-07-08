const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { DB_PATH } = require('./support/env');

module.exports = async () => {
  fs.rmSync(DB_PATH, { force: true });
  execFileSync('python3', [path.join(__dirname, 'seed_db.py')], {
    cwd: path.join(__dirname, '..'),
    env: { ...process.env, DB_PATH },
    stdio: 'inherit',
  });
};
