// Rendert die Recap-Mockups (recap_mock.html) als JPEGs.
// Vorher Server starten:  cd /home/ubuntu/faceit-weekend && python3 -m http.server 8899 --bind 127.0.0.1
// Ausführen:              node recap_mock/render.js
const pw = require('/home/ubuntu/paperclip/node_modules/.pnpm/playwright-core@1.62.1/node_modules/playwright-core');

(async () => {
  const browser = await pw.chromium.launch({
    executablePath: process.env.HOME + '/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome',
    args: ['--no-sandbox'],
  });
  // Avatare kommen von der FACEIT-CDN -> externe Requests hier NICHT blocken.
  const page = await browser.newPage({ viewport: { width: 2100, height: 2600 }, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:8899/recap_mock/recap_mock.html', { waitUntil: 'load' });
  await page.waitForFunction(() => document.title === 'READY', { timeout: 30000 }); // Template setzt READY, wenn Daten gerendert sind
  await page.waitForTimeout(1500); // Puffer für CDN-Avatare
  const out = '/home/ubuntu/faceit-weekend/recap_mock/';

  await page.locator('#team').screenshot({ path: out + 'recap_team.jpg', type: 'jpeg', quality: 92 });
  for (const nick of ['-neon666', 'theunc666', 'kokolorez', 'Shpooople', 'amaseling']) {
    await page.locator('.pcard:has-text("' + nick + '")')
      .screenshot({ path: out + 'recap_' + nick + '.jpg', type: 'jpeg', quality: 92 });
  }
  console.log('OK: 6 JPGs in ' + out);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
