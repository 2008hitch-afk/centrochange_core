const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

const EVIDENCE_DIR = path.resolve(__dirname, '../docs/evidence/issue-75/layout_density');
const ARTIFACT_DIR = '/home/empv26/.gemini/antigravity-cli/brain/b41de0d5-361b-4133-a26f-d99d267d4e08/evidence';

for (const dir of [EVIDENCE_DIR, ARTIFACT_DIR]) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

const CANDIDATE_JS = path.resolve(__dirname, '../app/centrochange_core/centrochange_core/public/premium/app.js');
const CANDIDATE_CSS = path.resolve(__dirname, '../app/centrochange_core/centrochange_core/public/premium/app.css');

if (!fs.existsSync(CANDIDATE_JS) || !fs.existsSync(CANDIDATE_CSS)) {
  console.error('Candidate built assets not found!');
  process.exit(1);
}

const CONTAINER = process.env.CC_TEST_CONTAINER || 'centrochange-dev-backend-1';
const SITE = process.env.CC_TEST_SITE || 'centrochange.local';
const BASE_URL = process.env.CC_TEST_BASE_URL || 'http://centrochange.local:8082';

function createEphemeralSessions(container, site) {
  const users = {
    m: 'cc-http-uat0000001-m@example.invalid',
    s: 'cc-http-uat0000001-s@example.invalid',
    f: 'cc-http-uat0000001-f@example.invalid',
    t: 'cc-http-uat0000001-t@example.invalid',
  };
  const script = `
import frappe, json
from werkzeug.test import EnvironBuilder
from frappe.sessions import Session

frappe.init("${site}")
frappe.connect()
frappe.request = EnvironBuilder().get_request()

res = {}
for role, email in ${JSON.stringify(users)}.items():
    sess = Session(user=email).start()
    res[role] = frappe.session.sid

frappe.db.commit()
print(json.dumps(res))
`;
  const raw = execSync(`docker exec -i -w /home/frappe/frappe-bench/sites ${container} /home/frappe/frappe-bench/env/bin/python`, {
    input: script,
    encoding: 'utf-8',
  });
  return JSON.parse(raw.trim());
}

function teardownEphemeralSessions(container, site, sids) {
  if (!sids || sids.length === 0) return;
  const script = `
import frappe, json
from frappe.sessions import delete_session

frappe.init("${site}")
frappe.connect()

for sid in ${JSON.stringify(sids)}:
    if sid:
        delete_session(sid=sid, reason="Teardown ephemeral test session")
print("cleaned")
`;
  try {
    execSync(`docker exec -i -w /home/frappe/frappe-bench/sites ${container} /home/frappe/frappe-bench/env/bin/python`, {
      input: script,
      encoding: 'utf-8',
    });
  } catch (err) {
    console.error('Warning: Error tearing down ephemeral sessions:', err.message);
  }
}

async function run() {
  console.log('=== STARTING UX #75 MULTI-VIEWPORT LAYOUT DENSITY VERIFICATION ===');
  const sessions = createEphemeralSessions(CONTAINER, SITE);
  const managerSid = sessions.m;

  const browser = await chromium.launch({
    executablePath: '/home/empv26/.cache/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-linux64/chrome-headless-shell',
    headless: true,
    args: ['--host-resolver-rules=MAP centrochange.local 127.0.0.1', '--no-proxy-server'],
  });

  const viewports = [
    { name: 'ultrawide_2560', width: 2560, height: 1440, isMobile: false },
    { name: 'desktop_1920', width: 1920, height: 1080, isMobile: false },
    { name: 'laptop_1440', width: 1440, height: 900, isMobile: false },
    { name: 'compact_1280', width: 1280, height: 800, isMobile: false },
    { name: 'tablet_1024', width: 1024, height: 768, isMobile: false },
    { name: 'mobile_390', width: 390, height: 844, isMobile: true },
    { name: 'mobile_375', width: 375, height: 667, isMobile: true },
  ];

  let totalChecks = 0;
  let passedChecks = 0;
  let failedChecks = 0;

  function assert(condition, message) {
    totalChecks++;
    if (condition) {
      passedChecks++;
      console.log(`  ✅ PASS: ${message}`);
    } else {
      failedChecks++;
      console.error(`  ❌ FAIL: ${message}`);
    }
  }

  try {
    for (const vp of viewports) {
      console.log(`\n=======================================================`);
      console.log(`=== AUDITING VIEWPORT: ${vp.name} (${vp.width}x${vp.height}) ===`);
      console.log(`=======================================================`);

      const context = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        isMobile: vp.isMobile,
      });

      await context.addCookies([
        {
          name: 'sid',
          value: managerSid,
          domain: 'centrochange.local',
          path: '/',
          httpOnly: false,
          secure: false,
          sameSite: 'Lax',
        },
      ]);

      const page = await context.newPage();

      // Intercept and serve candidate built assets
      await page.route('**/assets/centrochange_core/premium/app.js*', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/javascript',
          body: fs.readFileSync(CANDIDATE_JS),
        });
      });
      await page.route('**/assets/centrochange_core/premium/app.css*', route => {
        route.fulfill({
          status: 200,
          contentType: 'text/css',
          body: fs.readFileSync(CANDIDATE_CSS),
        });
      });

      const navTo = async (hash) => {
        await page.goto(`${BASE_URL}/premium#${hash}`, { waitUntil: 'networkidle' });
        await page.waitForTimeout(400);
      };

      // Navigate to initial view
      await navTo('Agenda');

      // Check global no-horizontal-scroll guard on initial load
      const initScroll = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }));
      assert(
        initScroll.scrollWidth <= initScroll.clientWidth + 1,
        `[${vp.name}] No global horizontal overflow on initial load (${initScroll.scrollWidth} <= ${initScroll.clientWidth})`
      );

      // --- 1. Audit Detailed Reports: Per paziente ---
      console.log(`--- [${vp.name}] Detailed Reports: Per paziente ---`);
      await navTo('Report');

      // Click "Compensi e fatture autorizzati"
      const reportBtn = page.locator('button:has-text("Compensi e fatture autorizzati")').first();
      await reportBtn.scrollIntoViewIfNeeded();
      await reportBtn.click();
      await page.waitForSelector('.finance-reports-page', { timeout: 6000 });

      // Switch to "Per paziente" tab
      await page.click('button:has-text("Per paziente")');
      await page.waitForTimeout(400);

      const reportsMetrics = await page.evaluate(() => {
        const pageEl = document.querySelector('.finance-reports-page');
        const detailSec = pageEl?.querySelector('.detail-section');
        const pickerList = pageEl?.querySelector('.patient-picker-list');
        const table = pickerList?.querySelector('table');
        const searchInput = pageEl?.querySelector('.search-inline input');
        const contentEl = document.querySelector('.content');

        return {
          pageWidth: pageEl?.getBoundingClientRect().width ?? 0,
          detailSecWidth: detailSec?.getBoundingClientRect().width ?? 0,
          contentWidth: contentEl?.getBoundingClientRect().width ?? 0,
          pickerListWidth: pickerList?.getBoundingClientRect().width ?? 0,
          tableWidth: table?.getBoundingClientRect().width ?? 0,
          searchWidth: searchInput?.getBoundingClientRect().width ?? 0,
          pickerScrollHeight: pickerList?.scrollHeight ?? 0,
          pickerClientHeight: pickerList?.clientHeight ?? 0,
          hasMaxHeight280: pickerList?.getAttribute('style')?.includes('280') ?? false,
          hasInnerScrollTrap: pickerList?.getAttribute('style')?.includes('overflow') ?? false,
        };
      });

      console.log(`    Content width: ${reportsMetrics.contentWidth}px | DetailSection width: ${reportsMetrics.detailSecWidth}px | Table width: ${reportsMetrics.tableWidth}px`);
      console.log(`    Picker maxHeight 280 removed: ${!reportsMetrics.hasMaxHeight280} | Inner scroll trap removed: ${!reportsMetrics.hasInnerScrollTrap}`);

      // Verify width utilization
      if (vp.width >= 1440) {
        assert(
          reportsMetrics.detailSecWidth > 980,
          `[${vp.name}] Detailed Reports: detailSection width (${reportsMetrics.detailSecWidth}px) exceeds former 980px clamp`
        );
      }
      assert(
        reportsMetrics.detailSecWidth >= reportsMetrics.pageWidth * 0.95,
        `[${vp.name}] Detailed Reports: detailSection utilizes >= 95% of container width (${reportsMetrics.detailSecWidth} / ${reportsMetrics.pageWidth})`
      );
      assert(
        !reportsMetrics.hasMaxHeight280 && !reportsMetrics.hasInnerScrollTrap,
        `[${vp.name}] Detailed Reports: patient-picker-list inner scroll trap & 280px clamp eliminated`
      );

      // Save screenshot for evidence
      const screen01 = path.join(ARTIFACT_DIR, `${vp.name}_01_reports_patient.png`);
      await page.screenshot({ path: screen01, fullPage: false });

      // Click on a patient in the picker to see the detailed patient report
      const firstPatientRow = page.locator('.patient-picker-list tr.clickable').first();
      if (await firstPatientRow.count() > 0) {
        await firstPatientRow.click();
        await page.waitForTimeout(600);

        const patientReportMetrics = await page.evaluate(() => {
          const metricsGrid = document.querySelector('.finance-report-metrics');
          const cards = metricsGrid?.querySelectorAll('.metric-card');
          const sessionTable = document.querySelector('.finance-reports-page table');
          const fiscalBanner = document.querySelector('.customer-fiscal-banner');
          const gridCols = metricsGrid ? window.getComputedStyle(metricsGrid).gridTemplateColumns.split(' ').length : 0;

          return {
            gridCols,
            cardCount: cards?.length ?? 0,
            tableWidth: sessionTable?.getBoundingClientRect().width ?? 0,
            bannerWidth: fiscalBanner?.getBoundingClientRect().width ?? 0,
          };
        });

        if (vp.width >= 1280) {
          assert(
            patientReportMetrics.gridCols >= 3,
            `[${vp.name}] Patient Report: metrics grid adapts to ${patientReportMetrics.gridCols} columns (not hardcoded to 2)`
          );
        }

        const screen02 = path.join(ARTIFACT_DIR, `${vp.name}_02_reports_patient_selected.png`);
        await page.screenshot({ path: screen02, fullPage: false });
      }

      // --- 2. Audit Detailed Reports: Per soggetto fiscale ---
      console.log(`--- [${vp.name}] Detailed Reports: Per soggetto fiscale ---`);
      await page.click('button:has-text("Per soggetto fiscale")');
      await page.waitForTimeout(500);

      const customerMetrics = await page.evaluate(() => {
        const table = document.querySelector('.finance-reports-page table');
        const detailSec = document.querySelector('.finance-reports-page .detail-section');
        return {
          tableWidth: table?.getBoundingClientRect().width ?? 0,
          secWidth: detailSec?.getBoundingClientRect().width ?? 0,
        };
      });

      if (vp.width >= 1440) {
        assert(
          customerMetrics.tableWidth > 980,
          `[${vp.name}] Customer Report: table width (${customerMetrics.tableWidth}px) exceeds former 980px clamp`
        );
      }
      assert(
        customerMetrics.tableWidth >= customerMetrics.secWidth * 0.90,
        `[${vp.name}] Customer Report: table width utilizes >= 90% of section width`
      );
      const screen03 = path.join(ARTIFACT_DIR, `${vp.name}_03_reports_customer.png`);
      await page.screenshot({ path: screen03, fullPage: false });

      // --- 3. Audit Patient Detail: Pagamenti Tab ---
      console.log(`--- [${vp.name}] Patient Scheda: Pagamenti tab ---`);
      await navTo('Pazienti');

      // Click first patient
      const patientRow = page.locator('tr.clickable').first();
      await patientRow.click();
      await page.waitForSelector('.patient-detail-page', { timeout: 6000 });

      // Click "Pagamenti" tab
      await page.click('.patient-page-tabs button:has-text("Pagamenti")');
      await page.waitForTimeout(500);

      const pagamentiMetrics = await page.evaluate(() => {
        const pagSec = document.querySelector('.patient-tab-payments');
        const pageEl = document.querySelector('.patient-detail-page');
        const metricsGrid = pagSec?.querySelector('.metrics-grid');
        const cards = metricsGrid?.querySelectorAll('.metric-card');
        const table = pagSec?.querySelector('table');
        const banner = pagSec?.querySelector('.customer-fiscal-banner');

        return {
          secWidth: pagSec?.getBoundingClientRect().width ?? 0,
          pageWidth: pageEl?.getBoundingClientRect().width ?? 0,
          gridWidth: metricsGrid?.getBoundingClientRect().width ?? 0,
          cardCount: cards?.length ?? 0,
          tableWidth: table?.getBoundingClientRect().width ?? 0,
          bannerWidth: banner?.getBoundingClientRect().width ?? 0,
        };
      });

      console.log(`    Patient Pagamenti width: ${pagamentiMetrics.secWidth}px | MetricsGrid width: ${pagamentiMetrics.gridWidth}px`);

      if (vp.width >= 1440) {
        assert(
          pagamentiMetrics.secWidth > 980,
          `[${vp.name}] Patient Pagamenti: width (${pagamentiMetrics.secWidth}px) exceeds former 980px clamp`
        );
      }
      assert(
        pagamentiMetrics.secWidth >= pagamentiMetrics.pageWidth * 0.95,
        `[${vp.name}] Patient Pagamenti: utilizes >= 95% of page container width`
      );
      const screen04 = path.join(ARTIFACT_DIR, `${vp.name}_04_patient_pagamenti.png`);
      await page.screenshot({ path: screen04, fullPage: false });

      // --- 4. Audit Patient Detail: Riepilogo & Sedute Tabs ---
      console.log(`--- [${vp.name}] Patient Scheda: Riepilogo & Sedute tabs ---`);
      await page.click('.patient-page-tabs button:has-text("Sedute")');
      await page.waitForTimeout(400);

      const seduteMetrics = await page.evaluate(() => {
        const sedSec = document.querySelector('.patient-tab-sessions');
        const table = sedSec?.querySelector('table');
        return {
          secWidth: sedSec?.getBoundingClientRect().width ?? 0,
          tableWidth: table?.getBoundingClientRect().width ?? 0,
        };
      });
      if (vp.width >= 1440 && seduteMetrics.tableWidth > 0) {
        assert(
          seduteMetrics.tableWidth > 980,
          `[${vp.name}] Patient Sedute: table (${seduteMetrics.tableWidth}px) exceeds former 980px clamp`
        );
      }

      await page.click('.patient-page-tabs button:has-text("Riepilogo")');
      await page.waitForTimeout(400);

      const riepilogoMetrics = await page.evaluate(() => {
        const propList = document.querySelector('.patient-tab-summary .property-list');
        const dt = propList?.querySelector('dt');
        return {
          propWidth: propList?.getBoundingClientRect().width ?? 0,
          dtWidth: dt?.getBoundingClientRect().width ?? 0,
        };
      });

      // Verify that property list does NOT stretch 1800px on desktop
      if (vp.width >= 1280) {
        assert(
          riepilogoMetrics.propWidth <= 860,
          `[${vp.name}] Patient Riepilogo: property-list maintains ergonomic width (${riepilogoMetrics.propWidth}px <= 860px)`
        );
      }

      // --- 5. Audit Service Catalog Detail ---
      console.log(`--- [${vp.name}] Service Catalog Detail ---`);
      await navTo('Servizi');

      const serviceRow = page.locator('tr.clickable').first();
      await serviceRow.click();
      await page.waitForSelector('.service-detail-page', { timeout: 6000 });

      const serviceMetrics = await page.evaluate(() => {
        const pageEl = document.querySelector('.service-detail-page');
        const sec = pageEl?.querySelector('.detail-section');
        const propList = sec?.querySelector('.property-list');
        return {
          pageWidth: pageEl?.getBoundingClientRect().width ?? 0,
          secWidth: sec?.getBoundingClientRect().width ?? 0,
          propWidth: propList?.getBoundingClientRect().width ?? 0,
        };
      });

      if (vp.width >= 1440) {
        assert(
          serviceMetrics.secWidth > 980,
          `[${vp.name}] Service Detail: section (${serviceMetrics.secWidth}px) exceeds former 980px clamp`
        );
      }
      assert(
        serviceMetrics.secWidth >= serviceMetrics.pageWidth * 0.95,
        `[${vp.name}] Service Detail: utilizes >= 95% of container width`
      );
      if (vp.width >= 1280) {
        assert(
          serviceMetrics.propWidth <= 860,
          `[${vp.name}] Service Detail: property-list keeps ergonomic width (${serviceMetrics.propWidth}px)`
        );
      }
      const screen05 = path.join(ARTIFACT_DIR, `${vp.name}_05_service_detail.png`);
      await page.screenshot({ path: screen05, fullPage: false });

      // --- 6. Audit AuditLog (Registro Modifiche) Detail ---
      console.log(`--- [${vp.name}] Audit Log Detail ---`);
      await navTo('Registro%20modifiche');

      const auditRow = page.locator('tr.clickable').first();
      if (await auditRow.count() > 0) {
        await auditRow.click();
        await page.waitForSelector('.audit-detail-page', { timeout: 6000 });

        const auditMetrics = await page.evaluate(() => {
          const pageEl = document.querySelector('.audit-detail-page');
          const sec = pageEl?.querySelector('.detail-section');
          return {
            secWidth: sec?.getBoundingClientRect().width ?? 0,
            pageWidth: pageEl?.getBoundingClientRect().width ?? 0,
          };
        });

        if (vp.width >= 1440) {
          assert(
            auditMetrics.secWidth > 980,
            `[${vp.name}] Audit Log: detail section (${auditMetrics.secWidth}px) exceeds former 980px clamp`
          );
        }
        assert(
          auditMetrics.secWidth >= auditMetrics.pageWidth * 0.95,
          `[${vp.name}] Audit Log: utilizes >= 95% of container width`
        );
        const screen06 = path.join(ARTIFACT_DIR, `${vp.name}_06_audit_log_detail.png`);
        await page.screenshot({ path: screen06, fullPage: false });
      }

      // --- 7. Audit Master Archives ---
      console.log(`--- [${vp.name}] Master Archives ---`);
      await navTo('Archivi');

      const archiveMetrics = await page.evaluate(() => {
        const layout = document.querySelector('.archive-layout');
        const menu = document.querySelector('.archive-menu');
        const panel = document.querySelector('.archive-panel');
        const table = panel?.querySelector('table');
        return {
          layoutWidth: layout?.getBoundingClientRect().width ?? 0,
          menuWidth: menu?.getBoundingClientRect().width ?? 0,
          panelWidth: panel?.getBoundingClientRect().width ?? 0,
          tableWidth: table?.getBoundingClientRect().width ?? 0,
        };
      });

      assert(
        archiveMetrics.panelWidth >= (archiveMetrics.layoutWidth - archiveMetrics.menuWidth - 40) * 0.90,
        `[${vp.name}] Archives: main panel utilizes available grid column cleanly`
      );
      const screen07 = path.join(ARTIFACT_DIR, `${vp.name}_07_master_archives.png`);
      await page.screenshot({ path: screen07, fullPage: false });

      // Final overflow check for this viewport
      const finalScroll = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }));
      assert(
        finalScroll.scrollWidth <= finalScroll.clientWidth + 1,
        `[${vp.name}] Final check: ZERO horizontal scrollbar on viewport (${finalScroll.scrollWidth} <= ${finalScroll.clientWidth})`
      );

      await context.close();
    }
  } finally {
    await browser.close();
    teardownEphemeralSessions(CONTAINER, SITE, Object.values(sessions));
    console.log('[AUTH] Ephemeral test sessions torn down cleanly.');
  }

  console.log('\n=======================================================');
  console.log('=== MULTI-VIEWPORT LAYOUT DENSITY VERIFICATION SUMMARY ===');
  console.log('=======================================================');
  console.log(`TOTAL: ${totalChecks} | PASS: ${passedChecks} | FAIL: ${failedChecks}`);

  if (failedChecks > 0) {
    process.exit(1);
  }
}

run().catch(err => {
  console.error('Fatal error during layout verification:', err);
  process.exit(1);
});
