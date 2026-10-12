// Issue #75: native-first role/responsive check on the single stack.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const fixture = JSON.parse(fs.readFileSync('/qa-fixture.json', 'utf8')).fixture;
const base = 'http://centrochange.local:8080';
const sizes = {desktop: {width: 1440, height: 900}, tablet: {width: 768, height: 900}, phone: {width: 390, height: 844}};
const roles = ['m', 's', 'a', 'b', 'c', 'f', 't'];
const expected = {
  m: ['Agenda', 'Ricerca pazienti', 'Anagrafica pazienti', 'Anagrafica professionisti', 'Finanza', 'Report professionisti', 'Report economico pazienti', 'Gestione accessi'],
  s: ['Agenda', 'Ricerca pazienti', 'Disponibilità', 'Notifiche', 'Finanza', 'Report professionisti'],
  a: ['Agenda', 'Ricerca pazienti', 'Disponibilità', 'Notifiche'],
  b: ['Agenda', 'Ricerca pazienti', 'Disponibilità', 'Notifiche'],
  c: ['Agenda', 'Ricerca pazienti', 'Disponibilità', 'Notifiche'],
  f: ['Finanza', 'Fatture pazienti', 'Incassi e pagamenti', 'Report professionisti'],
  t: ['Finanza', 'Fatture pazienti', 'Report economico pazienti']
};
const denied = {
  m: [], s: ['Gestione accessi', 'Registro modifiche', 'Anagrafica professionisti'],
  a: ['Finanza', 'Fatture pazienti', 'Gestione accessi', 'Anagrafica pazienti'],
  b: ['Finanza', 'Fatture pazienti', 'Gestione accessi', 'Anagrafica pazienti'],
  c: ['Finanza', 'Fatture pazienti', 'Gestione accessi', 'Anagrafica pazienti'],
  f: ['Agenda', 'Ricerca pazienti', 'Gestione accessi'],
  t: ['Agenda', 'Ricerca pazienti', 'Incassi e pagamenti', 'Gestione accessi']
};

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--host-resolver-rules=MAP centrochange.local 127.0.0.1', '--no-proxy-server', '--no-first-run']});
  const results = [];
  try {
    for (const role of roles) {
      const context = await browser.newContext({viewport: sizes.desktop, locale: 'it-IT'});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(base + '/login?redirect-to=/app/cc-unified-desk');
      await page.locator('#login_email').fill(fixture.users[role].name);
      await page.locator('#login_password').fill(fixture.users[role].password);
      await page.locator('.form-login button[type="submit"]').click();
      await page.locator('#cc-desk-sidebar').waitFor({timeout: 90000});
      await page.goto(base + '/app/cc-unified-desk?cc_view=home');
      await page.locator('.cc-desk-home').waitFor({timeout: 60000});
      assert.equal(await page.locator('#cc-desk-sidebar').count(), 1);
      assert.equal(await page.locator('#cc-desk-global-nav').count(), 1);
      assert.equal(await page.locator('.cc-desk-routebar').count(), 0);
      assert.equal(await page.locator('.cc-desk-home-action').count(), 3);
      assert.equal(await page.locator('#cc-tabler-core').count(), 0);
      const labels = await page.locator('#cc-desk-sidebar .cc-sidebar-link').allTextContents();
      for (const label of expected[role]) assert(labels.includes(label), `${role}: missing ${label}`);
      for (const label of denied[role]) assert(!labels.includes(label), `${role}: unexpected ${label}`);
      assert.equal(await page.locator('#cc-desk-sidebar [aria-current="page"]').count(), 1);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false, `${role}: desktop overflow`);
      await page.screenshot({path: `/qa-results/issue75-native-${role}-desktop.png`});
      if (role === 'm') {
        const account = page.locator('.cc-navbar-account');
        await account.locator('summary').click();
        assert.equal(await account.getAttribute('open'), '', 'account menu did not open');
        assert.equal(await account.locator('a').innerText(), 'Esci');
        await account.locator('summary').click();
        const section = page.locator('#cc-desk-sidebar details.cc-sidebar-group').filter({hasText: 'Amministrazione'});
        await section.locator('summary').focus();
        await page.keyboard.press('Enter');
        assert.equal(await section.getAttribute('open'), '', 'keyboard submenu did not open');
        assert.equal(await section.getByText('Fatture pazienti').isVisible(), true);
        const collapse = page.locator('.cc-sidebar-collapse');
        await collapse.click();
        assert.equal(await page.locator('body').evaluate(el => el.classList.contains('cc-sidebar-compact')), true);
        await collapse.click();
      }
      const target = ['m','s','a','b','c'].includes(role) ? 'Agenda' : 'Finanza';
      await page.locator('#cc-desk-sidebar .cc-sidebar-link').filter({hasText: target}).first().click();
      await page.waitForURL(url => url.searchParams.get('cc_view') === (target === 'Agenda' ? 'agenda' : 'finance'), {timeout: 60000});
      await page.locator('#cc-desk-sidebar').waitFor();
      assert.equal(await page.locator('#cc-desk-sidebar').count(), 1, `${role}: sidebar lost after custom navigation`);
      assert.equal(await page.locator('.cc-desk-routebar').count(), 0, `${role}: duplicate routebar`);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false, `${role}: route overflow`);
      if (role === 'm') {
        await page.goto(base + '/app/patient');
        await page.locator('#cc-desk-sidebar').waitFor();
        await page.waitForURL(/\/(app|desk)\/.*patient/, {timeout: 30000});
        await page.getByText('8 di 8').waitFor({timeout: 30000});
        assert.equal(await page.locator('#cc-desk-sidebar').count(), 1, 'native route lost sidebar');
        assert.equal(await page.locator('#cc-desk-sidebar [aria-current="page"]').innerText(), 'Anagrafica pazienti');
        await page.screenshot({path: '/qa-results/issue75-native-m-patient.png'});
        await page.locator('#cc-desk-sidebar .cc-sidebar-link').filter({hasText: 'Agenda'}).click();
        await page.waitForURL(url => url.searchParams.get('cc_view') === 'agenda', {timeout: 60000});
        await page.locator('#cc-desk-sidebar').waitFor();
        assert.equal(await page.locator('#cc-desk-sidebar').count(), 1, 'return from native route lost sidebar');
      }
      for (const [name, viewport] of Object.entries(sizes).filter(([name]) => name !== 'desktop')) {
        await page.setViewportSize(viewport);
        await page.goto(base + '/app/cc-unified-desk?cc_view=home');
        await page.locator('.cc-desk-home').waitFor();
        const toggle = page.locator('.cc-mobile-toggle');
        assert.equal(await toggle.isVisible(), true, `${role}: ${name} toggle hidden`);
        await toggle.focus();
        await page.keyboard.press('Enter');
        assert.equal(await toggle.getAttribute('aria-expanded'), 'true', `${role}: ${name} keyboard toggle`);
        await page.waitForFunction(() => document.querySelector('#cc-desk-sidebar').getBoundingClientRect().x >= -1);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false, `${role}: ${name} overflow`);
        await page.screenshot({path: `/qa-results/issue75-native-${role}-${name}.png`});
        await toggle.click();
      }
      assert.deepEqual(errors, [], `${role}: JavaScript page errors`);
      assert.equal(await page.evaluate(()=>getComputedStyle(document.body).fontFamily.includes('Times New Roman')),false,`${role}: Frappe CSS missing`);
      results.push({role, menu: labels.length, custom_navigation: target, native_navigation: role === 'm' ? 'Patient' : null, responsive: ['desktop','tablet','phone'], page_errors: errors});
      await context.close();
    }
    console.log(JSON.stringify({status: 'PASS', results}));
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack || error.message); process.exit(1); });
