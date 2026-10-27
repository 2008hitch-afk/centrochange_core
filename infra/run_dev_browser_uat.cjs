const { chromium } = require('playwright');
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const EVIDENCE_DIR = path.resolve(__dirname, '../docs/evidence/issue-171');
if (!fs.existsSync(EVIDENCE_DIR)) {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
}

function getSessionSid(email) {
  const cmd = `docker exec -w /home/frappe/frappe-bench/sites centrochange-dev-backend-1 /home/frappe/frappe-bench/env/bin/python -c '
import frappe
from werkzeug.test import EnvironBuilder
from frappe.sessions import Session
frappe.init("centrochange.local")
frappe.connect()
frappe.request = EnvironBuilder().get_request()
sess = Session(user="${email}").start()
sid = frappe.session.sid
frappe.db.commit()
print(sid)
'`;
  return execSync(cmd).toString().trim();
}

const USERS = {
  m: 'cc-http-uat0000001-m@example.invalid',
  s: 'cc-http-uat0000001-s@example.invalid',
  a: 'cc-http-uat0000001-a@example.invalid',
};

(async () => {
  console.log('[UAT] Launching headless Chromium browser...');
  const browser = await chromium.launch({
    headless: true,
    args: ['--host-resolver-rules=MAP centrochange.local 127.0.0.1', '--no-proxy-server']
  });

  const captured = [];

  async function createContextForUser(role) {
    const sid = getSessionSid(USERS[role]);
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
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

  try {
    // -------------------------------------------------------------
    // 1. MANAGER FLOWS (DESKTOP & MOBILE)
    // -------------------------------------------------------------
    console.log('[UAT] 1. Executing Manager Browser Flows...');
    const ctxM = await createContextForUser('m');
    const pageM = await ctxM.newPage();

    // 1A. Manager Agenda Calendar Popover
    await pageM.goto('http://centrochange.local:8082/premium#Agenda');
    await pageM.waitForLoadState('networkidle');
    await pageM.waitForTimeout(1000);

    // Open date popover / calendar button if available
    const calendarBtn = pageM.locator('button[aria-label="Apri calendario"], button:has-text("Scegli data")').first();
    if (await calendarBtn.isVisible()) {
      await calendarBtn.click();
      await pageM.waitForTimeout(500);
    }
    const shotAgendaM = path.join(EVIDENCE_DIR, 'dev-agenda-manager-calendar-desktop.png');
    await pageM.screenshot({ path: shotAgendaM, fullPage: false });
    captured.push('dev-agenda-manager-calendar-desktop.png');
    console.log('[UAT] Captured:', shotAgendaM);

    // 1B. Manager Report Desktop (Center Summary)
    await pageM.goto('http://centrochange.local:8082/premium#Report');
    await pageM.waitForLoadState('networkidle');
    await pageM.waitForTimeout(1200);

    const shotReportM = path.join(EVIDENCE_DIR, 'dev-report-manager-desktop.png');
    await pageM.screenshot({ path: shotReportM, fullPage: false });
    captured.push('dev-report-manager-desktop.png');
    console.log('[UAT] Captured:', shotReportM);

    // 1C. Manager Report Drilldown Desktop
    // Click on a KPI card to trigger drilldown filter
    const kpiCard = pageM.locator('button:has-text("Svolte"), button:has-text("Totali")').first();
    if (await kpiCard.isVisible()) {
      await kpiCard.click();
      await pageM.waitForTimeout(800);
    }
    // Click on an appointment row to open drawer if table row exists
    const apptRow = pageM.locator('table tbody tr').first();
    if (await apptRow.isVisible()) {
      await apptRow.click();
      await pageM.waitForTimeout(600);
    }
    const shotDrilldownM = path.join(EVIDENCE_DIR, 'dev-report-drilldown-desktop.png');
    await pageM.screenshot({ path: shotDrilldownM, fullPage: false });
    captured.push('dev-report-drilldown-desktop.png');
    console.log('[UAT] Captured:', shotDrilldownM);

    // Close the drawer before proceeding
    await pageM.keyboard.press('Escape');
    await pageM.waitForTimeout(500);

    // 1D. Manager Report Professionisti Toggle
    await pageM.goto('http://centrochange.local:8082/premium#Report');
    await pageM.reload();
    await pageM.waitForLoadState('networkidle');
    await pageM.waitForTimeout(1000);

    const profToggle = pageM.locator('button:has-text("Report professionisti"), input[type="checkbox"]#prof-toggle').first();
    if (await profToggle.isVisible()) {
      await profToggle.click();
      await pageM.waitForTimeout(800);
    }
    const shotProfReportM = path.join(EVIDENCE_DIR, 'dev-report-professionisti-desktop.png');
    await pageM.screenshot({ path: shotProfReportM, fullPage: false });
    captured.push('dev-report-professionisti-desktop.png');
    console.log('[UAT] Captured:', shotProfReportM);

    // 1E. Manager Report Mobile
    await pageM.setViewportSize({ width: 390, height: 844 });
    await pageM.waitForTimeout(600);
    const shotReportMMobile = path.join(EVIDENCE_DIR, 'dev-report-manager-mobile.png');
    await pageM.screenshot({ path: shotReportMMobile, fullPage: true });
    captured.push('dev-report-manager-mobile.png');
    console.log('[UAT] Captured:', shotReportMMobile);

    // 1F. Manager Professionals Directory (Desktop & Mobile)
    await pageM.setViewportSize({ width: 1440, height: 900 });
    await pageM.goto('http://centrochange.local:8082/premium#Professionisti');
    await pageM.waitForLoadState('networkidle');
    await pageM.waitForTimeout(1000);

    const shotProfM = path.join(EVIDENCE_DIR, 'dev-professionals-desktop.png');
    await pageM.screenshot({ path: shotProfM, fullPage: false });
    captured.push('dev-professionals-desktop.png');
    console.log('[UAT] Captured:', shotProfM);

    await pageM.setViewportSize({ width: 390, height: 844 });
    await pageM.waitForTimeout(600);
    const shotProfMMobile = path.join(EVIDENCE_DIR, 'dev-professionals-mobile.png');
    await pageM.screenshot({ path: shotProfMMobile, fullPage: true });
    captured.push('dev-professionals-mobile.png');
    console.log('[UAT] Captured:', shotProfMMobile);

    await ctxM.close();

    // -------------------------------------------------------------
    // 2. PROFESSIONAL A FLOWS (SCOPING & CLEAN NAVIGATION)
    // -------------------------------------------------------------
    console.log('[UAT] 2. Executing Professional A Browser Flows...');
    const ctxA = await createContextForUser('a');
    const pageA = await ctxA.newPage();

    // 2A. Professional A Scoped Agenda
    await pageA.goto('http://centrochange.local:8082/premium#Agenda');
    await pageA.waitForLoadState('networkidle');
    await pageA.waitForTimeout(1000);

    const shotAgendaA = path.join(EVIDENCE_DIR, 'dev-agenda-professional-desktop.png');
    await pageA.screenshot({ path: shotAgendaA, fullPage: false });
    captured.push('dev-agenda-professional-desktop.png');
    console.log('[UAT] Captured:', shotAgendaA);

    // 2B. Professional A Scoped Report Desktop
    await pageA.goto('http://centrochange.local:8082/premium#Report');
    await pageA.waitForLoadState('networkidle');
    await pageA.waitForTimeout(1000);

    const shotReportA = path.join(EVIDENCE_DIR, 'dev-report-professional-desktop.png');
    await pageA.screenshot({ path: shotReportA, fullPage: false });
    captured.push('dev-report-professional-desktop.png');
    console.log('[UAT] Captured:', shotReportA);

    // 2C. Professional A Scoped Report Mobile
    await pageA.setViewportSize({ width: 390, height: 844 });
    await pageA.waitForTimeout(600);
    const shotReportAMobile = path.join(EVIDENCE_DIR, 'dev-report-professional-mobile.png');
    await pageA.screenshot({ path: shotReportAMobile, fullPage: true });
    captured.push('dev-report-professional-mobile.png');
    console.log('[UAT] Captured:', shotReportAMobile);

    await ctxA.close();

    // -------------------------------------------------------------
    // 3. SECRETARIAT FLOWS
    // -------------------------------------------------------------
    console.log('[UAT] 3. Executing Secretariat Browser Flows...');
    const ctxS = await createContextForUser('s');
    const pageS = await ctxS.newPage();

    await pageS.goto('http://centrochange.local:8082/premium#Report');
    await pageS.waitForLoadState('networkidle');
    await pageS.waitForTimeout(1000);

    const shotReportS = path.join(EVIDENCE_DIR, 'dev-report-secretariat-desktop.png');
    await pageS.screenshot({ path: shotReportS, fullPage: false });
    captured.push('dev-report-secretariat-desktop.png');
    console.log('[UAT] Captured:', shotReportS);

    await ctxS.close();

    console.log('[UAT] Real browser tests and evidence capture completed successfully.');
    console.log(JSON.stringify({
      status: 'PASS_BROWSER_EVIDENCE',
      captured_count: captured.length,
      captured: captured
    }, null, 2));

  } catch (err) {
    console.error('[UAT] Browser test failed:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
