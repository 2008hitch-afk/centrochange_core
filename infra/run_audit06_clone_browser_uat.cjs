const { chromium } = require('playwright');
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const EVIDENCE_DIR = path.resolve(__dirname, '../docs/evidence/issue-177');
const ARTIFACT_DIR = '/home/empv26/.gemini/antigravity-cli/brain/e47cfc2a-4bab-4a41-ae20-ae6a02436fed/evidence';

for (const dir of [EVIDENCE_DIR, ARTIFACT_DIR]) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function getSessionSid(email) {
  const cmd = `docker exec -e FRAPPE_STREAM_LOGGING=1 -w /home/frappe/frappe-bench cc177-clone-backend /home/frappe/frappe-bench/env/bin/python -c '
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
'`;
  return execSync(cmd).toString().trim();
}

function discoverUsers() {
  const cmd = `docker exec -e FRAPPE_STREAM_LOGGING=1 -w /home/frappe/frappe-bench cc177-clone-backend /home/frappe/frappe-bench/env/bin/python -c '
import json, frappe
frappe.init("centrochange.local", sites_path="sites")
frappe.connect()

# CC Manager
managers = frappe.get_all("Has Role", filters={"role": "CC Manager", "parenttype": "User"}, fields=["parent"])
manager_email = managers[0].parent if managers else "Administrator"

# CC Professional
pros = frappe.get_all("Healthcare Practitioner", filters={"status": "Active"}, fields=["user_id"])
pro_emails = [p.user_id for p in pros if p.user_id]
pro_a = pro_emails[0] if pro_emails else manager_email
pro_b = pro_emails[1] if len(pro_emails) > 1 else pro_a

print(json.dumps({"manager": manager_email, "pro_a": pro_a, "pro_b": pro_b}))
'`;
  return JSON.parse(execSync(cmd).toString().trim());
}

(async () => {
  console.log('[BROWSER-UAT] Discovering users in isolated clone...');
  const users = discoverUsers();
  console.log('[BROWSER-UAT] Users:', users);

  console.log('[BROWSER-UAT] Launching headless Chromium against isolated clone port 8097...');
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
    // -------------------------------------------------------------
    // 1. SERVIZI (/premium/#Servizi) - Manager Desktop & Mobile
    // -------------------------------------------------------------
    console.log('[BROWSER-UAT] 1. /premium/#Servizi Desktop...');
    const ctxMgrDesktop = await createContext(users.manager, 1440, 900);
    const pageServizi = await ctxMgrDesktop.newPage();
    await pageServizi.goto('http://centrochange.local:8097/premium#Servizi');
    await pageServizi.waitForLoadState('networkidle');
    await pageServizi.waitForTimeout(1500);

    // Click first service row to open Drawer
    const firstRow = pageServizi.locator('.table-scroll tbody tr').first();
    if (await firstRow.isVisible()) {
      await firstRow.click();
      await pageServizi.waitForTimeout(1000);
    }
    await saveShot(pageServizi, 'audit06-servizi-desktop.png');

    console.log('[BROWSER-UAT] 1b. /premium/#Servizi Mobile...');
    const ctxMgrMobile = await createContext(users.manager, 390, 844);
    const pageServiziMob = await ctxMgrMobile.newPage();
    await pageServiziMob.goto('http://centrochange.local:8097/premium#Servizi');
    await pageServiziMob.waitForLoadState('networkidle');
    await pageServiziMob.waitForTimeout(1500);
    const firstRowMob = pageServiziMob.locator('.table-scroll tbody tr').first();
    if (await firstRowMob.isVisible()) {
      await firstRowMob.click();
      await pageServiziMob.waitForTimeout(1000);
    }
    await saveShot(pageServiziMob, 'audit06-servizi-mobile.png');

    // -------------------------------------------------------------
    // 2. DISPONIBILITÀ (/premium/#Disponibilità) - Professional Desktop & Mobile
    // -------------------------------------------------------------
    console.log('[BROWSER-UAT] 2. /premium/#Disponibilità Professional Desktop...');
    const ctxProDesktop = await createContext(users.pro_a, 1440, 900);
    const pageDisp = await ctxProDesktop.newPage();
    await pageDisp.goto('http://centrochange.local:8097/premium#Disponibilit%C3%A0');
    await pageDisp.waitForLoadState('networkidle');
    await pageDisp.waitForTimeout(1500);

    // Click "Modifica orario" button to open Schedule Modal
    const editBtn = pageDisp.getByRole('button', { name: 'Modifica orario' });
    if (await editBtn.isVisible()) {
      await editBtn.click();
      await pageDisp.waitForTimeout(1000);
    }
    await saveShot(pageDisp, 'audit06-disponibilita-modal-desktop.png');

    // Close modal, open "Registra assenza"
    const closeBtn = pageDisp.getByRole('button', { name: 'Indietro' });
    if (await closeBtn.isVisible()) {
      await closeBtn.click();
      await pageDisp.waitForTimeout(500);
    }
    const absenceBtn = pageDisp.getByRole('button', { name: 'Registra assenza' });
    if (await absenceBtn.isVisible()) {
      await absenceBtn.click();
      await pageDisp.waitForTimeout(1000);
    }
    await saveShot(pageDisp, 'audit06-assenza-modal-desktop.png');

    console.log('[BROWSER-UAT] 2b. /premium/#Disponibilità Mobile...');
    const ctxProMobile = await createContext(users.pro_a, 390, 844);
    const pageDispMob = await ctxProMobile.newPage();
    await pageDispMob.goto('http://centrochange.local:8097/premium#Disponibilit%C3%A0');
    await pageDispMob.waitForLoadState('networkidle');
    await pageDispMob.waitForTimeout(1500);

    const editBtnMob = pageDispMob.getByRole('button', { name: 'Modifica orario' });
    if (await editBtnMob.isVisible()) {
      await editBtnMob.click();
      await pageDispMob.waitForTimeout(1000);
    }
    await saveShot(pageDispMob, 'audit06-disponibilita-modal-mobile.png');

    // -------------------------------------------------------------
    // 3. ARCHIVI CATALOGO (/premium/#Archivi) - Manager Desktop & Mobile
    // -------------------------------------------------------------
    console.log('[BROWSER-UAT] 3. /premium/#Archivi Desktop...');
    const pageArchivi = await ctxMgrDesktop.newPage();
    await pageArchivi.goto('http://centrochange.local:8097/premium#Archivi');
    await pageArchivi.waitForLoadState('networkidle');
    await pageArchivi.waitForTimeout(1500);

    // Switch to Tariffe (Item Price) tab
    const tariffeTab = pageArchivi.getByRole('button', { name: 'Tariffe' }).or(pageArchivi.getByRole('tab', { name: 'Tariffe' })).first();
    if (await tariffeTab.isVisible()) {
      await tariffeTab.click();
      await pageArchivi.waitForTimeout(1000);
    }
    const archiveRow = pageArchivi.locator('.table-scroll tbody tr').first();
    if (await archiveRow.isVisible()) {
      await archiveRow.click();
      await pageArchivi.waitForTimeout(1000);
    }
    await saveShot(pageArchivi, 'audit06-archivi-tariffe-desktop.png');

    console.log('[BROWSER-UAT] 3b. /premium/#Archivi Mobile...');
    const pageArchiviMob = await ctxMgrMobile.newPage();
    await pageArchiviMob.goto('http://centrochange.local:8097/premium#Archivi');
    await pageArchiviMob.waitForLoadState('networkidle');
    await pageArchiviMob.waitForTimeout(1500);
    const tariffeTabMob = pageArchiviMob.getByRole('button', { name: 'Tariffe' }).or(pageArchiviMob.getByRole('tab', { name: 'Tariffe' })).first();
    if (await tariffeTabMob.isVisible()) {
      await tariffeTabMob.click();
      await pageArchiviMob.waitForTimeout(1000);
    }
    await saveShot(pageArchiviMob, 'audit06-archivi-tariffe-mobile.png');

    // -------------------------------------------------------------
    // 4. AGENDA REGRESSION (/premium/#Agenda) - Desktop & Mobile
    // -------------------------------------------------------------
    console.log('[BROWSER-UAT] 4. /premium/#Agenda Desktop...');
    const pageAgenda = await ctxMgrDesktop.newPage();
    await pageAgenda.goto('http://centrochange.local:8097/premium#Agenda');
    await pageAgenda.waitForLoadState('networkidle');
    await pageAgenda.waitForTimeout(1500);
    await saveShot(pageAgenda, 'audit06-agenda-snapshot-desktop.png');

    console.log('[BROWSER-UAT] 4b. /premium/#Agenda Mobile...');
    const pageAgendaMob = await ctxMgrMobile.newPage();
    await pageAgendaMob.goto('http://centrochange.local:8097/premium#Agenda');
    await pageAgendaMob.waitForLoadState('networkidle');
    await pageAgendaMob.waitForTimeout(1500);
    await saveShot(pageAgendaMob, 'audit06-agenda-snapshot-mobile.png');

    await ctxMgrDesktop.close();
    await ctxMgrMobile.close();
    await ctxProDesktop.close();
    await ctxProMobile.close();

    console.log(`[BROWSER-UAT] All screenshots captured successfully (${captured.length} shots).`);
  } finally {
    await browser.close();
  }
})();
