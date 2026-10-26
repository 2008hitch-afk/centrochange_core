const { chromium } = require('playwright');
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const EVIDENCE_DIR = path.resolve(__dirname, '../docs/evidence/issue-173');
const ARTIFACT_DIR = '/home/empv26/.gemini/antigravity-cli/brain/e47cfc2a-4bab-4a41-ae20-ae6a02436fed/evidence';

for (const dir of [EVIDENCE_DIR, ARTIFACT_DIR]) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
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
  a: 'cc-http-uat0000001-a@example.invalid', // CC Professional
  b: 'cc-http-uat0000001-b@example.invalid', // CC Professional B
  m: 'cc-http-uat0000001-m@example.invalid', // CC Manager
  s: 'cc-http-uat0000001-s@example.invalid', // CC Secretariat
};

(async () => {
  console.log('[DEV-UAT] Launching headless Chromium against live DEV port 8082...');
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
    const dest1 = path.join(EVIDENCE_DIR, filename);
    const dest2 = path.join(ARTIFACT_DIR, filename);
    await page.screenshot({ path: dest1, fullPage: false });
    fs.copyFileSync(dest1, dest2);
    const sz = fs.statSync(dest1).size;
    captured.push({ filename, size: sz });
    console.log(`[DEV-UAT] Saved screenshot: ${filename} (${sz} bytes)`);
  }

  try {
    // -------------------------------------------------------------
    // 1. PROFESSIONAL A - AGENDA & DAY CLOSURE MODAL (DESKTOP)
    // -------------------------------------------------------------
    console.log('[DEV-UAT] 1. Professional A Day Closure Modal (Desktop 1440x900)...');
    const ctxA = await createContext(USERS.a, 1440, 900);
    const pageA = await ctxA.newPage();
    await pageA.goto('http://centrochange.local:8082/premium#Agenda');
    await pageA.waitForLoadState('networkidle');
    await pageA.waitForTimeout(1000);

    const closeDayBtn = pageA.locator('button:has-text("Chiudi la mia giornata")').first();
    if (await closeDayBtn.isVisible()) {
      await closeDayBtn.click();
      await pageA.waitForSelector('.modal', { timeout: 5000 });
      await pageA.waitForTimeout(1000);
    }
    await saveShot(pageA, 'dev-core173-day-closure-modal-desktop.png');

    // -------------------------------------------------------------
    // 2. PROFESSIONAL A - DAY CLOSURE MODAL (MOBILE 390x844)
    // -------------------------------------------------------------
    console.log('[DEV-UAT] 2. Professional A Day Closure Modal (Mobile 390x844)...');
    const ctxAMobile = await createContext(USERS.a, 390, 844);
    const pageAMobile = await ctxAMobile.newPage();
    await pageAMobile.goto('http://centrochange.local:8082/premium#Agenda');
    await pageAMobile.waitForLoadState('networkidle');
    await pageAMobile.waitForTimeout(1000);

    const closeDayBtnMob = pageAMobile.locator('button:has-text("Chiudi la mia giornata")').first();
    if (await closeDayBtnMob.isVisible()) {
      await closeDayBtnMob.click();
      await pageAMobile.waitForSelector('.modal', { timeout: 5000 });
      await pageAMobile.waitForTimeout(1000);
    }
    await saveShot(pageAMobile, 'dev-core173-day-closure-modal-mobile.png');

    // -------------------------------------------------------------
    // 3. PROFESSIONAL A - ARREAR RECOVERY (DESKTOP)
    // -------------------------------------------------------------
    console.log('[DEV-UAT] 3. Professional A Arrear Recovery view in modal...');
    const arrearBadge = pageA.locator('.modal .arrear-badge').first();
    if (await arrearBadge.isVisible()) {
      console.log('[DEV-UAT] Clicking arrear badge:', await arrearBadge.innerText());
      await arrearBadge.click();
      await pageA.waitForTimeout(1000);
    }
    await saveShot(pageA, 'dev-core173-arrear-recovery-desktop.png');

    // Close modal
    const closeBtn = pageA.locator('.modal-head button[aria-label="Chiudi"]').first();
    if (await closeBtn.isVisible()) {
      await closeBtn.click();
      await pageA.waitForTimeout(500);
    }

    // -------------------------------------------------------------
    // 4. PROFESSIONAL A - REPORT & PARITY RECONCILIATION
    // -------------------------------------------------------------
    console.log('[DEV-UAT] 4. Professional A Reconciled Report (Desktop 1440x900)...');
    await pageA.goto('http://centrochange.local:8082/premium#Report');
    await pageA.waitForLoadState('networkidle');
    await pageA.waitForTimeout(1000);
    await saveShot(pageA, 'dev-core173-report-reconciled-desktop.png');

    console.log('[DEV-UAT] 5. Professional A Reconciled Report (Mobile 390x844)...');
    await pageAMobile.goto('http://centrochange.local:8082/premium#Report');
    await pageAMobile.waitForLoadState('networkidle');
    await pageAMobile.waitForTimeout(1000);
    await saveShot(pageAMobile, 'dev-core173-report-reconciled-mobile.png');

    // -------------------------------------------------------------
    // 6. MANAGER - OVERVIEW & AGENDA (DESKTOP)
    // -------------------------------------------------------------
    console.log('[DEV-UAT] 6. Manager Agenda Overview (Desktop 1440x900)...');
    const ctxM = await createContext(USERS.m, 1440, 900);
    const pageM = await ctxM.newPage();
    await pageM.goto('http://centrochange.local:8082/premium#Agenda');
    await pageM.waitForLoadState('networkidle');
    await pageM.waitForTimeout(1000);
    await saveShot(pageM, 'dev-core173-manager-agenda-desktop.png');

    console.log('[DEV-UAT] All screenshots captured successfully:');
    console.log(JSON.stringify(captured, null, 2));

  } finally {
    await browser.close();
  }
})();
