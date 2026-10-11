// Mission C isolated QA: one fresh Chromium per invocation, read-only navigation.
// Run with ROLE and ROUTE inside the verified 512 MiB QA container.
const {chromium} = require('playwright');
const fs = require('fs');

const fixture = JSON.parse(fs.readFileSync('/qa-fixture.json')).fixture;
const role = process.env.ROLE;
const route = process.env.ROUTE;
if (!role || !route || !/^\/app\/[a-z0-9-]+(?:\?[a-z0-9_=&%-]+)?$/.test(route) || !fixture.users[role]) {
  throw new Error('Invalid synthetic QA role or route');
}
const base = 'http://centrochange.local:8080';
const slug = `${role}-${route.split('/').pop().replace(/[^a-z0-9-]/gi, '-')}`;

(async () => {
  const browser = await chromium.launch({headless: true, timeout: 90000,
    args: [
      '--host-resolver-rules=MAP centrochange.local 127.0.0.1', '--no-proxy-server',
      '--no-first-run', '--disable-background-networking', '--disable-component-update',
      '--disable-default-apps', '--disable-sync', '--disable-extensions',
      '--disk-cache-size=0', '--media-cache-size=0',
    ]});
  const context = await browser.newContext({viewport: {width: 1440, height: 900}, locale: 'it-IT'});
  const page = await context.newPage();
  page.setDefaultTimeout(90000);
  page.setDefaultNavigationTimeout(90000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.goto(`${base}/login?redirect-to=${encodeURIComponent(route)}`);
    await page.locator('#login_email').fill(fixture.users[role].name);
    await page.locator('#login_password').fill(fixture.users[role].password);
    await page.locator('.form-login button[type="submit"]').click();
    try {
      await page.waitForFunction(() => (location.pathname.startsWith('/app') || location.pathname.startsWith('/desk'))
        && !!window.frappe,
        null, {timeout: 90000});
    } catch (error) {
      const diagnostic = {role, route, url: page.url(),
        title: await page.title(), body: (await page.locator('body').innerText()).slice(0, 500),
        errors};
      fs.writeFileSync(`/qa-results/native-failed-${slug}.json`, JSON.stringify(diagnostic, null, 2));
      throw error;
    }
    await page.waitForTimeout(4000);
    const result = await page.evaluate(() => ({
      url: location.pathname + location.search,
      title: document.title,
      bodyText: document.body.innerText.slice(0, 1400),
      overflow: document.documentElement.scrollWidth > innerWidth,
      route: window.frappe?.get_route?.() || null,
      clientDesk: document.body.classList.contains('cc-client-desk'),
      deskAsset: [...document.scripts].some(script => script.src.includes('cc_desk_client')),
      roleNames: window.frappe?.user_roles?.filter(role => role.startsWith('CC ')) || [],
      clientNav: [...document.querySelectorAll('#cc-desk-global-nav a')].map(link => ({
        text: link.textContent.trim(), href: link.getAttribute('href'), visible: !!link.getClientRects().length,
      })),
    }));
    result.role = role;
    result.requested = route;
    result.errors = errors;
    fs.writeFileSync(`/qa-results/native-${slug}.json`, JSON.stringify(result, null, 2));
    if (process.env.SCREENSHOT === '1') {
      await page.screenshot({path: `/qa-results/native-${slug}.png`, fullPage: false});
    }
    console.log(JSON.stringify({role, route, url: result.url, title: result.title,
      overflow: result.overflow, pageErrors: errors.length,
      clientDesk: result.clientDesk, clientNav: result.clientNav.map(link => link.text),
      deskAsset: result.deskAsset, roles: result.roleNames,
      accessDenied: /not permitted|permission|access denied|non autorizzato|non hai/i.test(result.bodyText)}));
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error.message); process.exit(1);});
