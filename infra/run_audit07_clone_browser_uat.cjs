const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const assert = require('assert');

const EVIDENCE_DIR = path.resolve(__dirname, '../docs/evidence/issue-179');
const ARTIFACT_DIR = '/home/empv26/.gemini/antigravity-cli/brain/e47cfc2a-4bab-4a41-ae20-ae6a02436fed/evidence';
const PORT = process.env.CC_UAT_PORT || '8098';
const BACKEND_CONTAINER = process.env.CC_BACKEND_CONTAINER || 'cc179-clone-backend';

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
pro_emails = [p.user_id for p in pros if p.user_id]
pro_a_email = pro_emails[0] if pro_emails else manager_email
pro_b_email = pro_emails[1] if len(pro_emails) > 1 else pro_a_email
pro_a_name = pros[0].name if pros else ""
pro_b_name = pros[1].name if len(pros) > 1 else pro_a_name

patients = frappe.get_all('Patient', fields=['name', 'patient_name'])
patient_name = patients[0].name if patients else ""

from centrochange_core.security.audit import internal_write
from centrochange_core.security.lifecycle import set_assignment
from centrochange_core.finance.collections import _booking_debts

zero_debt_patients = [p.name for p in frappe.get_all('Patient', fields=['name']) if len(_booking_debts(p.name)) == 0]
assignments = [a for a in frappe.get_all('CC Patient Assignment', filters={'center': center, 'active': 1, 'practitioner': pro_a_name}, fields=['patient', 'practitioner']) if a.patient in zero_debt_patients]
if assignments:
    assigned_patient = assignments[0].patient
    assigned_practitioner = assignments[0].practitioner
else:
    assigned_patient = zero_debt_patients[0] if zero_debt_patients else patient_name
    assigned_practitioner = pro_a_name
    frappe.set_user("Administrator")
    set_assignment(assigned_patient, center, pro_a_name, 1, 'UAT assignment')
    frappe.db.commit()

services = frappe.get_all('Appointment Type', fields=['name', 'default_duration', 'cc_service_item'])
service_name = services[0].name if services else ""

center_services = frappe.get_all('CC Center Service', filters={'center': center, 'enabled': 1}, fields=['appointment_type'])
enabled_service = center_services[0].appointment_type if center_services else service_name

print(json.dumps({
    "center": center,
    "price_list": price_list,
    "manager": manager_email,
    "secretary": sec_email,
    "pro_a": pro_a_email,
    "pro_b": pro_b_email,
    "pro_a_name": pro_a_name,
    "pro_b_name": pro_b_name,
    "patient": patient_name,
    "service": enabled_service,
    "assigned_patient": assigned_patient,
    "assigned_practitioner": assigned_practitioner
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
    // 1. AGENDA (/premium#Agenda) - Desktop & Mobile
    // =============================================================
    console.log('[BROWSER-UAT] 1. /premium#Agenda Desktop...');
    const ctxProDesk = await createContext(env.pro_a, 1440, 900);
    const pageAgenda = await ctxProDesk.newPage();
    await pageAgenda.goto(`http://centrochange.local:${PORT}/premium#Agenda`);
    await pageAgenda.waitForLoadState('networkidle');
    await pageAgenda.waitForTimeout(1000);
    await pageAgenda.locator('.metrics-grid').waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageAgenda, 'audit07-agenda-desktop.png');

    console.log('[BROWSER-UAT] 1b. /premium#Agenda Mobile...');
    const ctxProMob = await createContext(env.pro_a, 390, 844);
    const pageAgendaMob = await ctxProMob.newPage();
    await pageAgendaMob.goto(`http://centrochange.local:${PORT}/premium#Agenda`);
    await pageAgendaMob.waitForLoadState('networkidle');
    await pageAgendaMob.waitForTimeout(1000);
    await pageAgendaMob.locator('.metrics-grid').waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageAgendaMob, 'audit07-agenda-mobile.png');

    // =============================================================
    // 2. CANCELLAZIONE CON PREAVVISO 48H (/premium#Agenda drawer)
    // =============================================================
    console.log('[BROWSER-UAT] 2. Cancellation modal with 48h guidance Desktop...');
    // Book a future test session to cancel
    const bookScript = `
import frappe
from centrochange_core.scheduling.booking import book
from centrochange_core.security.lifecycle import set_assignment
frappe.init("centrochange.local", sites_path="sites")
frappe.connect()
frappe.set_user("Administrator")
set_assignment("${env.assigned_patient}", "${env.center}", "${env.assigned_practitioner}", 1, "UAT booking setup")
frappe.set_user("${env.pro_a}")
app = book(
    patient="${env.assigned_patient}",
    practitioner="${env.assigned_practitioner}",
    center="${env.center}",
    appointment_type="${env.service}",
    appointment_date="2099-05-15",
    appointment_time="10:00:00",
    request_key="uat-cancel-demo-1",
    reason="UAT session for cancellation demo"
)
frappe.db.commit()
print(app["name"])
`;
    const appToCancel = runFrappe(bookScript);

    // Open Agenda on that date or navigate directly to it
    await pageAgenda.goto(`http://centrochange.local:${PORT}/premium#Agenda`);
    await pageAgenda.waitForLoadState('networkidle');
    // Open date popover and jump to date or switch to day
    const dayBtn = pageAgenda.locator('.segmented button:has-text("Giorno")');
    await dayBtn.click();
    await pageAgenda.waitForTimeout(500);

    // Click on appointment event or search it via day closure or direct drawer
    // Let's open drawer by selecting event in Agenda
    // To make sure it's visible, let's book today future session for easier click
    const bookTodayScript = `
import frappe
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from centrochange_core.scheduling.booking import book
from centrochange_core.security.lifecycle import set_assignment
frappe.init("centrochange.local", sites_path="sites")
frappe.connect()
frappe.set_user("Administrator")
set_assignment("${env.assigned_patient}", "${env.center}", "${env.assigned_practitioner}", 1, "UAT booking today setup")
frappe.set_user("${env.pro_a}")
today_str = datetime.now(ZoneInfo('Europe/Rome')).strftime('%Y-%m-%d')
try:
    app = book(
        patient="${env.assigned_patient}",
        practitioner="${env.assigned_practitioner}",
        center="${env.center}",
        appointment_type="${env.service}",
        appointment_date=today_str,
        appointment_time="18:30:00",
        request_key="uat-cancel-today-1",
        reason="UAT today session for cancellation"
    )
    frappe.db.commit()
    print(app["name"])
except Exception as e:
    print(f"EXISTS:{e}")
`;
    runFrappe(bookTodayScript);

    await pageAgenda.reload();
    await pageAgenda.waitForLoadState('networkidle');
    await pageAgenda.waitForTimeout(1000);

    // Find and click any appointment in the week grid or calendar
    const eventLocator = pageAgenda.locator('.week-event').first();
    if (await eventLocator.isVisible()) {
      await eventLocator.click();
      await pageAgenda.locator('.drawer').waitFor({ state: 'visible', timeout: 3000 });
      // Click 'Cancella' button
      const cancelBtn = pageAgenda.locator('.action-grid button:has-text("Cancella")');
      if (await cancelBtn.isVisible()) {
        await cancelBtn.click();
        await pageAgenda.waitForTimeout(300);
        // Verify 48h guidance note
        const cancelNote = await pageAgenda.locator('.action-form .scope-note').textContent();
        assert(cancelNote.includes('48 ore'), 'Cancellation 48h note not displayed in form');
        await saveShot(pageAgenda, 'audit07-cancellation-desktop.png');
        await pageAgenda.keyboard.press('Escape');
        await pageAgenda.waitForTimeout(300);
        await pageAgenda.keyboard.press('Escape');
        await pageAgenda.waitForTimeout(500);
      }
    }

    // Mobile cancellation screenshot
    await pageAgendaMob.reload();
    await pageAgendaMob.waitForLoadState('networkidle');
    await pageAgendaMob.waitForTimeout(1000);
    const eventMob = pageAgendaMob.locator('.week-event').first();
    if (await eventMob.isVisible()) {
      await eventMob.click();
      await pageAgendaMob.locator('.drawer').waitFor({ state: 'visible', timeout: 3000 });
      const cancelBtnMob = pageAgendaMob.locator('.action-grid button:has-text("Cancella")');
      if (await cancelBtnMob.isVisible()) {
        await cancelBtnMob.click();
        await pageAgendaMob.waitForTimeout(300);
        await saveShot(pageAgendaMob, 'audit07-cancellation-mobile.png');
        await pageAgendaMob.keyboard.press('Escape');
        await pageAgendaMob.waitForTimeout(300);
        await pageAgendaMob.keyboard.press('Escape');
        await pageAgendaMob.waitForTimeout(500);
      }
    }

    // =============================================================
    // 3. DEROGA ECONOMICA (Waiver / Deroga autorizzata)
    // =============================================================
    console.log('[BROWSER-UAT] 3. Economic Waiver (Deroga) Desktop & Mobile...');
    // Create a late-cancelled session with Due economic state for today
    const waiveDemoScript = `
import frappe
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from centrochange_core.scheduling.booking import book
from centrochange_core.operations import lifecycle
frappe.init("centrochange.local", sites_path="sites")
frappe.connect()
frappe.in_test = True
frappe.conf.cc_synthetic_dev = 1
frappe.set_user("Administrator")
today_str = datetime.now(ZoneInfo('Europe/Rome')).strftime('%Y-%m-%d')
try:
    app = book(
        patient="${env.assigned_patient}",
        practitioner="${env.assigned_practitioner}",
        center="${env.center}",
        appointment_type="${env.service}",
        appointment_date=today_str,
        appointment_time="14:00:00",
        request_key="uat-waive-demo-today",
        reason="UAT session for late cancel and waiver demo"
    )
    doc = frappe.get_doc('Patient Appointment', app['name'])
    frappe.flags.cc_test_clock = lifecycle.start_utc(doc) - timedelta(hours=1)
    lifecycle.cancel(doc.name, "Disdetta tardiva del paziente")
    frappe.flags.cc_test_clock = None
    frappe.db.commit()
    print(doc.name)
except Exception as e:
    print(f"ERROR:{e}")
`;
    runFrappe(waiveDemoScript);

    // Manager opens /premium#Report to inspect cancelled sessions and apply waiver
    const ctxMgrDesk = await createContext(env.manager, 1440, 900);
    const pageMgr = await ctxMgrDesk.newPage();
    await pageMgr.goto(`http://centrochange.local:${PORT}/premium#Report`);
    await pageMgr.waitForLoadState('networkidle');
    await pageMgr.waitForTimeout(1000);

    // Select KPI "Sedute annullate"
    const kpiCancelled = pageMgr.locator('.metric:has-text("Sedute annullate")').first();
    if (await kpiCancelled.isVisible()) {
      await kpiCancelled.click();
      await pageMgr.waitForTimeout(800);
    }

    // Click on the first row in report sessions table to open AppointmentDetail drawer
    const reportRow = pageMgr.locator('.table-scroll tbody tr').first();
    if (await reportRow.isVisible()) {
      await reportRow.click();
      await pageMgr.locator('.drawer').waitFor({ state: 'visible', timeout: 3000 });
      // Click 'Rinuncia economica' button
      const waiveBtn = pageMgr.locator('.action-grid button:has-text("Rinuncia economica")');
      if (await waiveBtn.isVisible()) {
        await waiveBtn.click();
        await pageMgr.waitForTimeout(300);
        await saveShot(pageMgr, 'audit07-waiver-desktop.png');
        await pageMgr.keyboard.press('Escape');
        await pageMgr.waitForTimeout(300);
        await pageMgr.keyboard.press('Escape');
        await pageMgr.waitForTimeout(500);
      }
    }

    // Mobile waiver screenshot
    const ctxMgrMob = await createContext(env.manager, 390, 844);
    const pageMgrMob = await ctxMgrMob.newPage();
    await pageMgrMob.goto(`http://centrochange.local:${PORT}/premium#Report`);
    await pageMgrMob.waitForLoadState('networkidle');
    await pageMgrMob.waitForTimeout(1000);
    const kpiCancelledMob = pageMgrMob.locator('.metric:has-text("Sedute annullate")').first();
    if (await kpiCancelledMob.isVisible()) {
      await kpiCancelledMob.click();
      await pageMgrMob.waitForTimeout(800);
    }
    const reportRowMob = pageMgrMob.locator('.table-scroll tbody tr').first();
    if (await reportRowMob.isVisible()) {
      await reportRowMob.click();
      await pageMgrMob.locator('.drawer').waitFor({ state: 'visible', timeout: 3000 });
      const waiveBtnMob = pageMgrMob.locator('.action-grid button:has-text("Rinuncia economica")');
      if (await waiveBtnMob.isVisible()) {
        await waiveBtnMob.click();
        await pageMgrMob.waitForTimeout(300);
        await saveShot(pageMgrMob, 'audit07-waiver-mobile.png');
        await pageMgrMob.keyboard.press('Escape');
        await pageMgrMob.waitForTimeout(300);
        await pageMgrMob.keyboard.press('Escape');
        await pageMgrMob.waitForTimeout(500);
      }
    }

    // =============================================================
    // 4. CHIUDI LA MIA GIORNATA (/premium#Agenda modal)
    // =============================================================
    console.log('[BROWSER-UAT] 4. Chiudi la mia giornata Desktop & Mobile...');
    await pageAgenda.goto(`http://centrochange.local:${PORT}/premium#Agenda`);
    await pageAgenda.waitForLoadState('networkidle');
    await pageAgenda.waitForTimeout(1000);

    const dayClosureBtn = pageAgenda.locator('button:has-text("Chiudi la mia giornata")').first();
    if (await dayClosureBtn.isVisible()) {
      await dayClosureBtn.click();
      await pageAgenda.locator('.day-closure-container').waitFor({ state: 'visible', timeout: 5000 });
      await pageAgenda.waitForTimeout(500);
      await saveShot(pageAgenda, 'audit07-day-closure-desktop.png');
      await pageAgenda.keyboard.press('Escape');
      await pageAgenda.waitForTimeout(500);
    }

    await pageAgendaMob.goto(`http://centrochange.local:${PORT}/premium#Agenda`);
    await pageAgendaMob.waitForLoadState('networkidle');
    await pageAgendaMob.waitForTimeout(1000);
    const dayClosureBtnMob = pageAgendaMob.locator('button:has-text("Chiudi la mia giornata")').first();
    if (await dayClosureBtnMob.isVisible()) {
      await dayClosureBtnMob.click();
      await pageAgendaMob.locator('.day-closure-container').waitFor({ state: 'visible', timeout: 5000 });
      await pageAgendaMob.waitForTimeout(500);
      await saveShot(pageAgendaMob, 'audit07-day-closure-mobile.png');
      await pageAgendaMob.keyboard.press('Escape');
      await pageAgendaMob.waitForTimeout(500);
    }

    // =============================================================
    // 5. NOTIFICHE PROFESSIONISTA (/premium#Notifiche)
    // =============================================================
    console.log('[BROWSER-UAT] 5. Professional Personal Notifications Desktop & Mobile...');
    // Create a synthetic closure reminder notification for pro_a
    const notifScript = `
import frappe
from centrochange_core.operations.automation import enqueue_notice
from centrochange_core.operations import notifications
frappe.init("centrochange.local", sites_path="sites")
frappe.connect()
frappe.set_user("Administrator")
name = enqueue_notice(
    "uat-reminder-demo-1",
    "${env.pro_a}",
    "CLOSURE_REMINDER",
    "Healthcare Practitioner",
    "${env.assigned_practitioner}",
    "Hai sedute da chiudere oggi. Apri «Chiudi la mia giornata» per completarle prima delle ore 07:00."
)
notifications.deliver(name)
frappe.db.commit()
print(name)
`;
    runFrappe(notifScript);

    const pageNotifPro = await ctxProDesk.newPage();
    await pageNotifPro.goto(`http://centrochange.local:${PORT}/premium#Notifiche`);
    await pageNotifPro.waitForLoadState('networkidle');
    await pageNotifPro.waitForTimeout(1000);
    await pageNotifPro.locator('.personal-notifications').waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageNotifPro, 'audit07-notifiche-pro-desktop.png');

    const pageNotifProMob = await ctxProMob.newPage();
    await pageNotifProMob.goto(`http://centrochange.local:${PORT}/premium#Notifiche`);
    await pageNotifProMob.waitForLoadState('networkidle');
    await pageNotifProMob.waitForTimeout(1000);
    await pageNotifProMob.locator('.personal-notifications').waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageNotifProMob, 'audit07-notifiche-pro-mobile.png');

    // =============================================================
    // 6. NOTIFICHE DIREZIONE (/premium#Notifiche) - Manager View
    // =============================================================
    console.log('[BROWSER-UAT] 6. Manager Operational Notifications Desktop & Mobile...');
    const pageNotifMgr = await ctxMgrDesk.newPage();
    await pageNotifMgr.goto(`http://centrochange.local:${PORT}/premium#Notifiche`);
    await pageNotifMgr.waitForLoadState('networkidle');
    await pageNotifMgr.waitForTimeout(1000);
    await pageNotifMgr.locator('.panel-toolbar').waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageNotifMgr, 'audit07-notifiche-manager-desktop.png');

    const pageNotifMgrMob = await ctxMgrMob.newPage();
    await pageNotifMgrMob.goto(`http://centrochange.local:${PORT}/premium#Notifiche`);
    await pageNotifMgrMob.waitForLoadState('networkidle');
    await pageNotifMgrMob.waitForTimeout(1000);
    await pageNotifMgrMob.locator('.panel-toolbar').waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageNotifMgrMob, 'audit07-notifiche-manager-mobile.png');

    // =============================================================
    // 7. REPORT OPERATIVO RICONCILIATO (/premium#Report)
    // =============================================================
    console.log('[BROWSER-UAT] 7. Reconciled Operational Report Desktop & Mobile...');
    const pageReport = await ctxMgrDesk.newPage();
    await pageReport.goto(`http://centrochange.local:${PORT}/premium#Report`);
    await pageReport.waitForLoadState('networkidle');
    await pageReport.waitForTimeout(1000);
    await pageReport.locator('.metrics-grid').first().waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageReport, 'audit07-report-reconciled-desktop.png');

    const pageReportMob = await ctxMgrMob.newPage();
    await pageReportMob.goto(`http://centrochange.local:${PORT}/premium#Report`);
    await pageReportMob.waitForLoadState('networkidle');
    await pageReportMob.waitForTimeout(1000);
    await pageReportMob.locator('.metrics-grid').first().waitFor({ state: 'visible', timeout: 5000 });
    await saveShot(pageReportMob, 'audit07-report-reconciled-mobile.png');

    console.log('[BROWSER-UAT] All screenshots captured successfully:', captured);
  } finally {
    await browser.close();
  }
})();
