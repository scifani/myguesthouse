// Regression test for the ROSS1000 export design flaw: exporting a date
// range must pull from Storico Ospiti (the registered_guests history, via
// /api/guests/history) rather than whatever happens to be in the in-page
// check-in form. See e2e/seed_db.py for the seeded fixture guests.
const { test, expect, FIXTURE_APARTMENT } = require('./support/fixtures');

test('exports guests from history for the selected date range', async ({ adminPage: page }) => {
  await page.locator('#ross_start').fill('2026-05-10');
  await page.locator('#ross_end').fill('2026-05-20');

  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: /Genera XML ROSS1000/i }).click();
  const download = await downloadPromise;

  expect(download.suggestedFilename()).toBe(`${FIXTURE_APARTMENT.rossCodice}_2026-05-10_2026-05-20.xml`);

  const stream = await download.createReadStream();
  const xml = await new Promise((resolve, reject) => {
    const chunks = [];
    stream.on('data', (c) => chunks.push(c));
    stream.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    stream.on('error', reject);
  });

  // Fully inside the range: must be present as a full arrival record.
  expect(xml).toContain('<cognome>INRANGE</cognome>');

  // Arrived before the range but still checked in when it opens (arrival
  // 2026-05-08 + 3 nights -> departs 2026-05-11): this is the exact case
  // the old "only look at the current check-in form" logic missed. The
  // ROSS1000 <partenza> record has no name field (arrival was presumably
  // reported in a prior export), so we confirm it via occupancy + the
  // departure record referencing its original arrival date instead.
  const day10 = xml.match(/<data>20260510<\/data>[\s\S]*?<\/movimento>/)[0];
  expect(day10).toMatch(/<camereoccupate>1<\/camereoccupate>/);
  const day11 = xml.match(/<data>20260511<\/data>[\s\S]*?<\/movimento>/)[0];
  expect(day11).toContain('<arrivo>20260508</arrivo>');

  // Entirely outside the range: must be absent.
  expect(xml).not.toContain('OUTOFRANGE');
});

test('rejects export when no guests fall in the selected range', async ({ adminPage: page }) => {
  await page.locator('#ross_start').fill('2026-01-01');
  await page.locator('#ross_end').fill('2026-01-05');

  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: /Genera XML ROSS1000/i }).click();
  // No download event should fire; the alert above is the only feedback.
  await expect(page.locator('#rossInfo')).toBeVisible();
});
