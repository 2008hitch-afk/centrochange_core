const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const assert = require('assert');

const EVIDENCE_DIR = path.resolve(__dirname, '../docs/evidence/issue-183');
const ARTIFACT_DIR = process.env.CC_ARTIFACT_DIR || path.resolve(__dirname, '../.audit09-browser-artifacts');
const PORT = process.env.CC_UAT_PORT || '8099';
const BACKEND_CONTAINER = process.env.CC_BACKEND_CONTAINER || 'cc183-clone-backend';

for (const dir of [EVIDENCE_DIR, ARTIFACT_DIR]) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function runFrappe(code) {
  const out = execFileSync(
    'docker',
    ['exec', '-e', 'FRAPPE_STREAM_LOGGING=1', '-w', '/home/frappe/frappe-bench',
     BACKEND_CONTAINER, '/home/frappe/frappe-bench/env/bin/python', '-c', code],
    { encoding: 'utf-8' }
  );
  return out.trim();
}

function getSessionSid(email) {
  const code = `
import frappe
from werkzeug.test import EnvironBuilder
from frappe.sessions import Session
frappe.init("centrochange.local", sites_path="sites")
frappe.connect()
frappe.request = EnvironBuilder().get_request()
sess = Session(user="${email}").start()
sid = frappe.session.sid
frappe.db.commit()
print(sid)
`;
  return runFrappe(code);
}

function discoverEnvironment() {
  const code = `
import json, frappe
frappe.init("centrochange.local", sites_path="sites")
frappe.connect()

operational_centers = frappe.get_all('Branch', filters={'cc_operational': 1}, fields=['name', 'cc_price_list'], order_by='name asc')
center = operational_centers[0].name if operational_centers else ""
price_list = operational_centers[0].cc_price_list if operational_centers else ""

member_users = [m.user for m in frappe.get_all('CC Center Membership', filters={'center': center, 'active': 1}, fields=['user'])]
managers = frappe.get_all('Has Role', filters={'role': 'CC Manager', 'parenttype': 'User', 'parent': ['in', member_users]}, fields=['parent'])
manager_email = managers[0].parent if managers else 'Administrator'

secretaries = frappe.get_all('Has Role', filters={'role': 'CC Secretariat', 'parenttype': 'User', 'parent': ['in', member_users]}, fields=['parent'])
sec_email = secretaries[0].parent if secretaries else manager_email

pros = frappe.get_all('Healthcare Practitioner', filters={'status': 'Active', 'user_id': ['in', member_users]}, fields=['name', 'user_id', 'practitioner_name'])
pro_emails = [p.user_id for p in pros if p.user_id]
pro_a_email = pro_emails[0] if pro_emails else manager_email
pro_a_name = pros[0].name if pros else ""

print(json.dumps({
    "center": center,
    "price_list": price_list,
    "manager": manager_email,
    "secretary": sec_email,
    "pro_a": pro_a_email,
    "pro_a_name": pro_a_name
}))
`;
  return JSON.parse(runFrappe(code));
}

(async () => {
  console.log(`[BROWSER-UAT] Discovering environment in ${BACKEND_CONTAINER}...`);
  const env = discoverEnvironment();
  console.log('[BROWSER-UAT] Environment:', env);

  console.log(`[BROWSER-UAT] Launching Chromium against port ${PORT}...`);
  const browser = await chromium.launch({
    headless: true,
    args: ['--host-resolver-rules=MAP centrochange.local 127.0.0.1', '--no-proxy-server']
  });

  const captured = [];

  async function createContext(email, width = 1440, height = 900) {
    const sid = getSessionSid(email);
    const context = await browser.newContext({
      viewport: { width, height },
      locale: 'it-IT',
      timezoneId: 'Europe/Rome'
    });
    await context.addCookies([{
      name: 'sid',
      value: sid,
      domain: 'centrochange.local',
      path: '/'
    }]);
    return context;
  }

  async function saveShot(page, filename) {
    const dest = path.join(EVIDENCE_DIR, filename);
    const artDest = path.join(ARTIFACT_DIR, filename);
    await page.screenshot({ path: dest, fullPage: false });
    if (dest !== artDest) fs.copyFileSync(dest, artDest);
    captured.push(filename);
    console.log(`[BROWSER-UAT] Saved screenshot: ${dest} & ${artDest}`);
  }

  async function waitForList(page, label) {
    try {
      await page.locator('.archive-panel tbody tr').first().waitFor({ state: 'visible', timeout: 15000 });
    } catch (error) {
      const panel = await page.locator('.archive-panel').innerText().catch(() => '<archive panel absent>');
      console.error(`[BROWSER-UAT] ${label}: list did not render at ${page.url()}: ${panel.slice(0, 2000)}`);
      await saveShot(page, `audit09-failure-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.png`);
      throw error;
    }
  }

  async function openArchives(page) {
    await page.goto(`http://centrochange.local:${PORT}/premium#Archivi`, { waitUntil: 'networkidle' });
    const centerPicker = page.locator('.center-selector select');
    await centerPicker.waitFor({ state: 'visible', timeout: 15000 });
    await centerPicker.selectOption(env.center);
    await page.waitForSelector('.archive-layout', { timeout: 15000 });
    await page.locator('.archive-panel .panel-title p').filter({ hasText: 'Centro A' }).waitFor({ state: 'visible', timeout: 15000 });
  }

  try {
    // =============================================================
    // 1. PATIENTS ARCHIVE & DETAIL DRAWER (Desktop 1440x900)
    // =============================================================
    console.log('[BROWSER-UAT] 1. Manager Patient Detail Drawer Desktop...');
    {
      const context = await createContext(env.manager, 1440, 900);
      const page = await context.newPage();
      await openArchives(page);
      await page.waitForSelector('.table-scroll', { timeout: 15000 });
      await page.waitForTimeout(500);

      // Open Patient detail drawer
      const firstRow = page.locator('.table-scroll tbody tr').first();
      if (await firstRow.isVisible()) {
        await firstRow.click();
        await page.waitForSelector('.drawer-content, .offcanvas, .property-list', { timeout: 5000 });
        await page.waitForTimeout(500);
        await saveShot(page, 'audit09-pazienti-detail-drawer-desktop.png');

        // Close drawer
        const closeBtn = page.locator('button[aria-label="Chiudi"], .btn-close, button:has-text("Chiudi")').first();
        if (await closeBtn.isVisible()) {
          await closeBtn.click();
          await page.waitForTimeout(300);
        }
      }

      // 2. Perform server-side search
      console.log('[BROWSER-UAT] 2. Manager /premium#Archivi Desktop Search...');
      const searchInput = page.locator('input[type="search"]').first();
      if (await searchInput.isVisible()) {
        await searchInput.fill('Mar');
        await page.waitForTimeout(800); // debounce wait
        await saveShot(page, 'audit09-pazienti-search-desktop.png');
      }

      await context.close();
    }

    // =============================================================
    // 3. PRACTITIONERS ARCHIVE (Desktop 1440x900)
    // =============================================================
    console.log('[BROWSER-UAT] 3. Manager Practitioner Archive Desktop...');
    {
      const context = await createContext(env.manager, 1440, 900);
      const page = await context.newPage();
      await openArchives(page);
      await page.locator('.archive-menu button[aria-label="Professionisti"]').click();
      await waitForList(page, 'Professionisti');
      await page.waitForTimeout(500);

      await saveShot(page, 'audit09-professionisti-list-desktop.png');
      await context.close();
    }

    // =============================================================
    // 4. CENTER SERVICES CATALOG (Desktop 1440x900)
    // =============================================================
    console.log('[BROWSER-UAT] 4. Manager Center Service Catalog Desktop...');
    {
      const context = await createContext(env.manager, 1440, 900);
      const page = await context.newPage();
      await openArchives(page);
      await page.locator('.archive-menu button[aria-label="Servizi del centro"]').click();
      await page.waitForSelector('.table-scroll', { timeout: 15000 });
      await page.waitForTimeout(500);

      await saveShot(page, 'audit09-catalogo-servizi-desktop.png');
      await context.close();
    }

    // =============================================================
    // 5. ITEM PRICE / TARIFFS (Desktop 1440x900)
    // =============================================================
    console.log('[BROWSER-UAT] 5. Manager Item Price Desktop...');
    {
      const context = await createContext(env.manager, 1440, 900);
      const page = await context.newPage();
      await openArchives(page);
      await page.locator('.archive-menu button[aria-label="Tariffe"]').click();
      await page.waitForSelector('.table-scroll', { timeout: 15000 });
      await page.waitForTimeout(500);

      await saveShot(page, 'audit09-tariffe-desktop.png');
      await context.close();
    }

    // =============================================================
    // 6. SALES INVOICE WITH ITALIAN DOCSTATUS & DRAWER (Desktop 1440x900)
    // =============================================================
    console.log('[BROWSER-UAT] 6. Manager Sales Invoice Italian Docstatus Desktop...');
    {
      const context = await createContext(env.manager, 1440, 900);
      const page = await context.newPage();
      await openArchives(page);
      await page.locator('.archive-menu button[aria-label="Fatture pazienti"]').click();
      await page.waitForSelector('.table-scroll', { timeout: 15000 });
      await page.waitForTimeout(500);

      // Click first row to view drawer with Italian docstatus
      const firstRow = page.locator('.table-scroll tbody tr').first();
      if (await firstRow.isVisible()) {
        await firstRow.click();
        await page.waitForSelector('.drawer-content, .offcanvas, .property-list', { timeout: 5000 });
        await page.waitForTimeout(500);
      }

      await saveShot(page, 'audit09-fatture-pazienti-docstatus-desktop.png');
      await context.close();
    }

    // =============================================================
    // 7. PAYMENT ENTRY READ-ONLY (Desktop 1440x900)
    // =============================================================
    console.log('[BROWSER-UAT] 7. Manager Payment Entry Read-Only Desktop...');
    {
      const context = await createContext(env.manager, 1440, 900);
      const page = await context.newPage();
      await openArchives(page);
      await page.locator('.archive-menu button[aria-label="Pagamenti"]').click();
      await page.waitForSelector('.table-scroll', { timeout: 15000 });
      await page.waitForTimeout(500);

      await saveShot(page, 'audit09-pagamenti-readonly-desktop.png');
      await context.close();
    }

    // =============================================================
    // 8. PATIENTS ARCHIVE (Mobile 390x844)
    // =============================================================
    console.log('[BROWSER-UAT] 8. Manager Patient Archive Mobile...');
    {
      const context = await createContext(env.manager, 390, 844);
      const page = await context.newPage();
      await openArchives(page);
      await page.waitForTimeout(500);

      await saveShot(page, 'audit09-pazienti-mobile.png');
      await context.close();
    }

    // =============================================================
    // 9. SALES INVOICE (Mobile 390x844)
    // =============================================================
    console.log('[BROWSER-UAT] 9. Manager Sales Invoice Mobile...');
    {
      const context = await createContext(env.manager, 390, 844);
      const page = await context.newPage();
      await openArchives(page);
      await page.locator('.archive-menu button[aria-label="Fatture pazienti"]').click();
      await page.waitForSelector('.table-scroll', { timeout: 15000 });
      await page.waitForTimeout(500);

      await saveShot(page, 'audit09-fatture-mobile.png');
      await context.close();
    }

    // Every archive must expose a real list row and a real detail drawer, at both
    // approved viewport sizes. A screenshot alone is never a functional PASS.
    const archives = [
      ['Pazienti', 'patient'], ['Professionisti', 'practitioner'],
      ['Articoli', 'item'], ['Tariffe', 'price'], ['Tipi seduta', 'appointment-type'],
      ['Servizi del centro', 'center-service'], ['Modelli pacchetto', 'package-template'],
      ['Fatture pazienti', 'sales-invoice'], ['Fatture professionisti', 'purchase-invoice'],
      ['Pagamenti', 'payment-entry'], ['Movimenti bancari', 'bank-transaction']
    ];
    for (const [width, height, viewport] of [[1440, 900, 'desktop'], [390, 844, 'mobile']]) {
      const context = await createContext(env.manager, width, height);
      const page = await context.newPage();
      await openArchives(page);
      for (const [label, slug] of archives) {
        await page.locator(`.archive-menu button[aria-label="${label}"]`).click();
        await waitForList(page, label);
        assert.strictEqual(await page.locator('.archive-panel [role="alert"]').count(), 0, `${label}: list error`);
        await page.locator('.archive-panel tbody tr').first().click();
        await page.locator('.drawer[role="dialog"] .property-list').waitFor({ state: 'visible', timeout: 10000 });
        assert.ok(await page.locator('.drawer[role="dialog"] .property-list dt').count() > 0, `${label}: empty detail`);
        await saveShot(page, `audit09-${slug}-detail-${viewport}.png`);
        await page.locator('.drawer[role="dialog"] button[aria-label="Chiudi"]').click();
      }
      await context.close();
    }

    console.log(`[BROWSER-UAT] Successfully completed all 11 archive list/detail checks at desktop/mobile. Screenshots:`, captured);
  } finally {
    await browser.close();
  }
})().catch(err => {
  console.error('[BROWSER-UAT] FATAL:', err);
  process.exit(1);
});
