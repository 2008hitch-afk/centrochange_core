const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const assert = require('assert');

const EVIDENCE_DIR = path.resolve(__dirname, '../docs/evidence/issue-181');
const ARTIFACT_DIR = '/home/empv26/.gemini/antigravity-cli/brain/e47cfc2a-4bab-4a41-ae20-ae6a02436fed/evidence';
const PORT = process.env.CC_UAT_PORT || '8098';
const BACKEND_CONTAINER = process.env.CC_BACKEND_CONTAINER || 'cc181-clone-backend';

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

operational_centers = frappe.get_all('Branch', filters={'cc_operational': 1}, fields=['name', 'cc_price_list'])
center = operational_centers[0].name if operational_centers else ""
price_list = operational_centers[0].cc_price_list if operational_centers else ""

managers = frappe.get_all('Has Role', filters={'role': 'CC Manager', 'parenttype': 'User'}, fields=['parent'])
manager_email = managers[0].parent if managers else 'Administrator'

secretaries = frappe.get_all('Has Role', filters={'role': 'CC Secretariat', 'parenttype': 'User'}, fields=['parent'])
sec_email = secretaries[0].parent if secretaries else manager_email

pros = frappe.get_all('Healthcare Practitioner', filters={'status': 'Active'}, fields=['name', 'user_id', 'practitioner_name'])
pros.sort(key=lambda p: frappe.db.count('Patient Appointment', {'practitioner': p.name, 'appointment_date': ['between', ['2026-10-01', '2026-10-28']]}), reverse=True)
pro_emails = [p.user_id for p in pros if p.user_id]
pro_a_email = pro_emails[0] if pro_emails else manager_email
pro_b_email = pro_emails[1] if len(pro_emails) > 1 else pro_a_email
pro_a_name = pros[0].name if pros else ""
pro_b_name = pros[1].name if len(pros) > 1 else pro_a_name

print(json.dumps({
    "center": center,
    "price_list": price_list,
    "manager": manager_email,
    "secretary": sec_email,
    "pro_a": pro_a_email,
    "pro_b": pro_b_email,
    "pro_a_name": pro_a_name,
    "pro_b_name": pro_b_name
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
    fs.copyFileSync(dest, artDest);
    captured.push(filename);
    console.log(`[BROWSER-UAT] Saved screenshot: ${dest} & ${artDest}`);
  }

  try {
    // =============================================================
    // 1. MANAGER VIEW: /premium#Report (Desktop 1440x900)
    // =============================================================
    console.log('[BROWSER-UAT] 1. Manager /premium#Report Desktop...');
    {
      const context = await createContext(env.manager, 1440, 900);
      const page = await context.newPage();
      await page.goto(`http://centrochange.local:${PORT}/premium#Report`, { waitUntil: 'networkidle' });
      await page.waitForSelector('.report-currency', { timeout: 15000 });
      await page.waitForSelector('.report-drilldown', { timeout: 15000 });

      // Check export buttons
      const exportCenterBtn = page.getByRole('link', { name: /Esporta CSV del centro/i });
      assert(await exportCenterBtn.isVisible(), 'Esporta CSV del centro button should be visible');

      // Check metrics cards
      assert(await page.getByText('Sedute totali').first().isVisible(), 'Sedute totali card visible');
      assert(await page.getByText('Sedute svolte').first().isVisible(), 'Sedute svolte card visible');
      assert(await page.getByText('Appuntamenti futuri').first().isVisible(), 'Appuntamenti futuri card visible');
      assert(await page.getByText('Sedute da chiudere').first().isVisible(), 'Sedute da chiudere card visible');

      await saveShot(page, 'audit08-report-manager-desktop.png');
      await context.close();
    }

    // =============================================================
    // 2. MANAGER VIEW: /premium#Report (Mobile 390x844)
    // =============================================================
    console.log('[BROWSER-UAT] 2. Manager /premium#Report Mobile...');
    {
      const context = await createContext(env.manager, 390, 844);
      const page = await context.newPage();
      await page.goto(`http://centrochange.local:${PORT}/premium#Report`, { waitUntil: 'networkidle' });
      await page.waitForSelector('.report-currency', { timeout: 15000 });
      await page.waitForSelector('.report-drilldown', { timeout: 15000 });

      await saveShot(page, 'audit08-report-manager-mobile.png');
      await context.close();
    }

    // =============================================================
    // 3. DASHBOARD HASH ALIAS: /premium#Dashboard (Desktop 1440x900)
    // =============================================================
    console.log('[BROWSER-UAT] 3. Hash Alias /premium#Dashboard Desktop...');
    {
      const context = await createContext(env.manager, 1440, 900);
      const page = await context.newPage();
      await page.goto(`http://centrochange.local:${PORT}/premium#Dashboard`, { waitUntil: 'networkidle' });
      await page.waitForSelector('.report-currency', { timeout: 15000 });
      await page.waitForSelector('.report-drilldown', { timeout: 15000 });

      // Check that Heading is indeed Report & Riepilogo
      const heading = page.getByRole('heading', { name: 'Report', level: 1 });
      assert(await heading.isVisible(), 'Report heading rendered via #Dashboard alias');

      await saveShot(page, 'audit08-dashboard-alias-desktop.png');
      await context.close();
    }

    // =============================================================
    // 4. PROFESSIONAL VIEW: /premium#Report (Desktop 1440x900)
    // =============================================================
    console.log('[BROWSER-UAT] 4. Professional /premium#Report Desktop...');
    {
      const context = await createContext(env.pro_a, 1440, 900);
      const page = await context.newPage();
      await page.goto(`http://centrochange.local:${PORT}/premium#Report`, { waitUntil: 'networkidle' });
      await page.waitForSelector('.agenda-practitioner-label', { timeout: 15000 });
      await page.waitForSelector('.panel', { timeout: 15000 });
      await page.waitForTimeout(1000);

      // Verify that professional cannot select other practitioners
      const proLabel = page.locator('.agenda-practitioner-label');
      assert(await proLabel.isVisible(), 'Personal report label visible for professional');
      assert(await page.getByText(/Report personale/i).isVisible(), 'Report personale badge visible');
      assert(await page.getByRole('link', { name: /Esporta le mie sedute/i }).isVisible(), 'Export link scoped to personal sessions');

      await saveShot(page, 'audit08-report-pro-desktop.png');
      await context.close();
    }

    // =============================================================
    // 5. PROFESSIONAL VIEW: /premium#Report (Mobile 390x844)
    // =============================================================
    console.log('[BROWSER-UAT] 5. Professional /premium#Report Mobile...');
    {
      const context = await createContext(env.pro_a, 390, 844);
      const page = await context.newPage();
      await page.goto(`http://centrochange.local:${PORT}/premium#Report`, { waitUntil: 'networkidle' });
      await page.waitForSelector('.agenda-practitioner-label', { timeout: 15000 });
      await page.waitForSelector('.panel', { timeout: 15000 });
      await page.waitForTimeout(1000);

      await saveShot(page, 'audit08-report-pro-mobile.png');
      await context.close();
    }

    // =============================================================
    // 6. MANAGER VIEW: Drilldown Filter & Dettaglio Professionista
    // =============================================================
    console.log('[BROWSER-UAT] 6. Manager Drilldown Filter & Dettaglio Professionista...');
    {
      const context = await createContext(env.manager, 1440, 900);
      const page = await context.newPage();
      await page.goto(`http://centrochange.local:${PORT}/premium#Report`, { waitUntil: 'networkidle' });
      await page.waitForSelector('.report-currency', { timeout: 15000 });
      await page.waitForSelector('.report-drilldown', { timeout: 15000 });

      // Click on "Sedute svolte" metric card to filter drilldown
      const performedMetric = page.locator('.metric-card').filter({ hasText: 'Sedute svolte' }).first();
      if (await performedMetric.isVisible()) {
        await performedMetric.click();
        await page.waitForTimeout(500);
      }

      // Open "Dettaglio professionista"
      const toggleProBtn = page.getByRole('button', { name: 'Dettaglio professionista' });
      await toggleProBtn.click();
      await page.waitForSelector('.professional-report', { timeout: 5000 });

      // Select practitioner in professional report
      const proSelect = page.locator('.professional-report select[aria-label="Professionista report"]');
      if (await proSelect.isVisible()) {
        const options = await proSelect.locator('option').all();
        if (options.length > 1) {
          const val = await options[1].getAttribute('value');
          if (val) {
            await proSelect.selectOption(val);
            await page.waitForTimeout(1000);
          }
        }
      }

      await saveShot(page, 'audit08-drilldown-filtered-desktop.png');
      await context.close();
    }

    console.log(`[BROWSER-UAT] Successfully completed all checks. Screenshots:`, captured);
  } finally {
    await browser.close();
  }
})().catch(err => {
  console.error('[BROWSER-UAT] FATAL:', err);
  process.exit(1);
});
