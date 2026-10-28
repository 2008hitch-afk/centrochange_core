const { chromium } = require('playwright');
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const EVIDENCE_DIR = path.resolve(__dirname, '../docs/evidence/issue-179');
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
    // 1. PROFESSIONAL A - AGENDA & DAY CLOSURE MODAL (DESKTOP & MOBILE)
    // -------------------------------------------------------------
    console.log('[DEV-UAT] 1. Professional A Agenda Desktop...');
    const ctxA = await createContext(USERS.a, 1440, 900);
    const pageA = await ctxA.newPage();
    await pageA.goto('http://centrochange.local:8082/premium#Agenda');
    await pageA.waitForLoadState('networkidle');
    await pageA.waitForTimeout(1000);
    await saveShot(pageA, 'dev-audit07-agenda-desktop.png');

    console.log('[DEV-UAT] 1b. Professional A Day Closure Modal Desktop...');
    const closeDayBtn = pageA.locator('button:has-text("Chiudi la mia giornata")').first();
    if (await closeDayBtn.isVisible()) {
      await closeDayBtn.click();
      await pageA.locator('.day-closure-container').waitFor({ state: 'visible', timeout: 5000 });
      await pageA.waitForTimeout(500);
      await saveShot(pageA, 'dev-audit07-day-closure-desktop.png');
      await pageA.keyboard.press('Escape');
      await pageA.waitForTimeout(500);
    }

    console.log('[DEV-UAT] 1c. Professional A Agenda & Day Closure Mobile...');
    const ctxAMobile = await createContext(USERS.a, 390, 844);
    const pageAMobile = await ctxAMobile.newPage();
    await pageAMobile.goto('http://centrochange.local:8082/premium#Agenda');
    await pageAMobile.waitForLoadState('networkidle');
    await pageAMobile.waitForTimeout(1000);
    await saveShot(pageAMobile, 'dev-audit07-agenda-mobile.png');

    const closeDayBtnMob = pageAMobile.locator('button:has-text("Chiudi la mia giornata")').first();
    if (await closeDayBtnMob.isVisible()) {
      await closeDayBtnMob.click();
      await pageAMobile.locator('.day-closure-container').waitFor({ state: 'visible', timeout: 5000 });
      await pageAMobile.waitForTimeout(500);
      await saveShot(pageAMobile, 'dev-audit07-day-closure-mobile.png');
      await pageAMobile.keyboard.press('Escape');
      await pageAMobile.waitForTimeout(500);
    }

    // -------------------------------------------------------------
    // 2. CANCELLATION DRAWER WITH 48H GUIDANCE (DESKTOP & MOBILE)
    // -------------------------------------------------------------
    console.log('[DEV-UAT] 2. Cancellation Drawer with 48h Guidance Desktop...');
    // Click on the first event in calendar or first row in week view
    const eventItem = pageA.locator('.rbc-event, .session-cell, .week-grid-appointment').first();
    if (await eventItem.isVisible()) {
      await eventItem.click();
      await pageA.locator('.drawer').waitFor({ state: 'visible', timeout: 4000 });
      const cancelBtn = pageA.locator('.action-grid button:has-text("Annulla seduta")').first();
      if (await cancelBtn.isVisible()) {
        await cancelBtn.click();
        await pageA.waitForTimeout(500);
        await saveShot(pageA, 'dev-audit07-cancellation-desktop.png');
        await pageA.keyboard.press('Escape');
        await pageA.waitForTimeout(300);
      }
      await pageA.keyboard.press('Escape');
      await pageA.waitForTimeout(500);
    }

    console.log('[DEV-UAT] 2b. Cancellation Drawer Mobile...');
    const eventItemMob = pageAMobile.locator('.rbc-event, .session-cell, .week-grid-appointment').first();
    if (await eventItemMob.isVisible()) {
      await eventItemMob.click();
      await pageAMobile.locator('.drawer').waitFor({ state: 'visible', timeout: 4000 });
      const cancelBtnMob = pageAMobile.locator('.action-grid button:has-text("Annulla seduta")').first();
      if (await cancelBtnMob.isVisible()) {
        await cancelBtnMob.click();
        await pageAMobile.waitForTimeout(500);
        await saveShot(pageAMobile, 'dev-audit07-cancellation-mobile.png');
        await pageAMobile.keyboard.press('Escape');
        await pageAMobile.waitForTimeout(300);
      }
      await pageAMobile.keyboard.press('Escape');
      await pageAMobile.waitForTimeout(500);
    }

    // -------------------------------------------------------------
    // 3. PROFESSIONAL A PERSONAL NOTIFICATIONS (DESKTOP & MOBILE)
    // -------------------------------------------------------------
    console.log('[DEV-UAT] 3. Professional A Personal Notifications Desktop & Mobile...');
    const pageNotifPro = await ctxA.newPage();
    await pageNotifPro.goto('http://centrochange.local:8082/premium#Notifiche');
    await pageNotifPro.waitForLoadState('networkidle');
    await pageNotifPro.waitForTimeout(1000);
    await pageNotifPro.locator('.personal-notifications').waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageNotifPro, 'dev-audit07-notifiche-pro-desktop.png');

    const pageNotifProMob = await ctxAMobile.newPage();
    await pageNotifProMob.goto('http://centrochange.local:8082/premium#Notifiche');
    await pageNotifProMob.waitForLoadState('networkidle');
    await pageNotifProMob.waitForTimeout(1000);
    await pageNotifProMob.locator('.personal-notifications').waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageNotifProMob, 'dev-audit07-notifiche-pro-mobile.png');

    // -------------------------------------------------------------
    // 4. MANAGER OPERATIONAL NOTIFICATIONS (DESKTOP & MOBILE)
    // -------------------------------------------------------------
    console.log('[DEV-UAT] 4. Manager Operational Notifications Desktop & Mobile...');
    const ctxM = await createContext(USERS.m, 1440, 900);
    const pageNotifMgr = await ctxM.newPage();
    await pageNotifMgr.goto('http://centrochange.local:8082/premium#Notifiche');
    await pageNotifMgr.waitForLoadState('networkidle');
    await pageNotifMgr.waitForTimeout(1000);
    await pageNotifMgr.locator('.panel-toolbar').first().waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageNotifMgr, 'dev-audit07-notifiche-manager-desktop.png');

    const ctxMMobile = await createContext(USERS.m, 390, 844);
    const pageNotifMgrMob = await ctxMMobile.newPage();
    await pageNotifMgrMob.goto('http://centrochange.local:8082/premium#Notifiche');
    await pageNotifMgrMob.waitForLoadState('networkidle');
    await pageNotifMgrMob.waitForTimeout(1000);
    await pageNotifMgrMob.locator('.panel-toolbar').first().waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageNotifMgrMob, 'dev-audit07-notifiche-manager-mobile.png');

    // -------------------------------------------------------------
    // 5. MANAGER RECONCILED OPERATIONAL REPORT (DESKTOP & MOBILE)
    // -------------------------------------------------------------
    console.log('[DEV-UAT] 5. Manager Reconciled Operational Report Desktop & Mobile...');
    const pageReport = await ctxM.newPage();
    await pageReport.goto('http://centrochange.local:8082/premium#Report');
    await pageReport.waitForLoadState('networkidle');
    await pageReport.waitForTimeout(1000);
    await pageReport.locator('.metrics-grid').first().waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageReport, 'dev-audit07-report-reconciled-desktop.png');

    const pageReportMob = await ctxMMobile.newPage();
    await pageReportMob.goto('http://centrochange.local:8082/premium#Report');
    await pageReportMob.waitForLoadState('networkidle');
    await pageReportMob.waitForTimeout(1000);
    await pageReportMob.locator('.metrics-grid').first().waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageReportMob, 'dev-audit07-report-reconciled-mobile.png');

    console.log('[DEV-UAT] All screenshots captured successfully:', captured);
  } finally {
    await browser.close();
  }
})();