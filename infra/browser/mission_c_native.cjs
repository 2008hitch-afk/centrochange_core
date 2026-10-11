// Mission C isolated QA: one fresh Chromium per invocation, read-only navigation.
// Run with ROLE and ROUTE inside the verified 512 MiB QA container.
const {chromium} = require('playwright');
const fs = require('fs');

const fixture = JSON.parse(fs.readFileSync('/qa-fixture.json')).fixture;
const role = process.env.ROLE;
const route = process.env.ROUTE;
if (!role || !route || !/^\/app\/[a-z0-9-]+$/.test(route) || !fixture.users[role]) {
  throw new Error('Invalid synthetic QA role or route');
}
const base = 'http://centrochange.local:8080';
const slug = `${role}-${route.split('/').pop()}`;

(async () => {
  const browser = await chromium.launch({headless: true,
    args: ['--host-resolver-rules=MAP centrochange.local 127.0.0.1', '--no-proxy-server']});
  const context = await browser.newContext({viewport: {width: 1440, height: 900}, locale: 'it-IT'});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.goto(`${base}/login?redirect-to=${encodeURIComponent(route)}`);
    await page.locator('#login_email').fill(fixture.users[role].name);
    await page.locator('#login_password').fill(fixture.users[role].password);
    await page.locator('.form-login button[type="submit"]').click();
    await page.waitForTimeout(4500);
    const result = await page.evaluate(() => ({
      url: location.pathname + location.search,
      title: document.title,
      bodyText: document.body.innerText.slice(0, 1400),
      overflow: document.documentElement.scrollWidth > innerWidth,
      route: window.frappe?.get_route?.() || null,
      clientDesk: document.body.classList.contains('cc-client-desk'),
      clientNav: [...document.querySelectorAll('#cc-desk-global-nav a')].map(link => ({
        text: link.textContent.trim(), href: link.getAttribute('href'), visible: !!link.getClientRects().length,
      })),
    }));
    result.role = role;
    result.requested = route;
    result.errors = errors;
    fs.writeFileSync(`/qa-results/native-${slug}.json`, JSON.stringify(result, null, 2));
    await page.screenshot({path: `/qa-results/native-${slug}.png`, fullPage: false});
    console.log(JSON.stringify({role, route, url: result.url, title: result.title,
      overflow: result.overflow, pageErrors: errors.length,
      clientDesk: result.clientDesk, clientNav: result.clientNav.map(link => link.text),
      accessDenied: /not permitted|permission|access denied|non autorizzato|non hai/i.test(result.bodyText)}));
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error.message); process.exit(1);});
