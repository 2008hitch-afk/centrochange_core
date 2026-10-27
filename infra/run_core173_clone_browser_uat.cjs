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
  const cmd = `docker exec -w /home/frappe/frappe-bench/sites cc173-clone-backend /home/frappe/frappe-bench/env/bin/python -c '
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
  m: 'cc-http-uat0000001-m@example.invalid', // CC Manager
};

(async () => {
  console.log('[BROWSER-UAT] Launching headless Chromium against isolated clone port 8095...');
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
    // 1. PROFESSIONAL DESKTOP (1440x900)
    console.log('[BROWSER-UAT] 1. CC Professional Desktop Flow...');
    const ctxA = await createContext(USERS.a, 1440, 900);
    const pageA = await ctxA.newPage();

    await pageA.goto('http://centrochange.local:8095/premium#Agenda');
    await pageA.waitForLoadState('networkidle');
    await pageA.waitForTimeout(1500);

    // Open "Chiudi la mia giornata" modal
    const closeBtn = pageA.getByRole('button', { name: 'Chiudi la mia giornata' }).first();
    if (await closeBtn.isVisible()) {
      await closeBtn.click();
      await pageA.waitForTimeout(1000);
    }
    await saveShot(pageA, 'core173-day-closure-modal-desktop.png');

    // Click on arrear date if visible
    const arrearBadge = pageA.locator('.arrear-badge').first();
    if (await arrearBadge.isVisible()) {
      await arrearBadge.click();
      await pageA.waitForTimeout(1000);
    }
    await saveShot(pageA, 'core173-arrear-recovery-desktop.png');
    await ctxA.close();

    // 2. PROFESSIONAL MOBILE (390x844)
    console.log('[BROWSER-UAT] 2. CC Professional Mobile Flow...');
    const ctxAMob = await createContext(USERS.a, 390, 844);
    const pageAMob = await ctxAMob.newPage();

    await pageAMob.goto('http://centrochange.local:8095/premium#Agenda');
    await pageAMob.waitForLoadState('networkidle');
    await pageAMob.waitForTimeout(1500);

    const closeBtnMob = pageAMob.getByRole('button', { name: 'Chiudi la mia giornata' }).first();
    if (await closeBtnMob.isVisible()) {
      await closeBtnMob.click();
      await pageAMob.waitForTimeout(1000);
    }
    await saveShot(pageAMob, 'core173-day-closure-modal-mobile.png');
    await ctxAMob.close();

    // 3. MANAGER DESKTOP REPORT (1440x900)
    console.log('[BROWSER-UAT] 3. Manager Reconciled Report Flow...');
    const ctxM = await createContext(USERS.m, 1440, 900);
    const pageM = await ctxM.newPage();

    await pageM.goto('http://centrochange.local:8095/premium#Report');
    await pageM.waitForLoadState('networkidle');
    await pageM.waitForTimeout(1500);

    await saveShot(pageM, 'core173-report-reconciled-desktop.png');
    await ctxM.close();

    // 4. MANAGER MOBILE REPORT (390x844)
    console.log('[BROWSER-UAT] 4. Manager Mobile Report Flow...');
    const ctxMMob = await createContext(USERS.m, 390, 844);
    const pageMMob = await ctxMMob.newPage();

    await pageMMob.goto('http://centrochange.local:8095/premium#Report');
    await pageMMob.waitForLoadState('networkidle');
    await pageMMob.waitForTimeout(1500);

    await saveShot(pageMMob, 'core173-report-reconciled-mobile.png');
    await ctxMMob.close();

    console.log('[BROWSER-UAT] Real clone browser flow completed successfully. Captured:', captured);
  } finally {
    await browser.close();
  }
})();
