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
confirmed_invoice = frappe.get_all('Sales Invoice', filters={'cc_center': center, 'docstatus': 1, 'name': ['not like', 'CC9-%']}, pluck='name', limit_page_length=1)[0]
cancelled_invoice = frappe.get_all('Sales Invoice', filters={'cc_center': center, 'docstatus': 2, 'name': ['like', 'CC9-%']}, pluck='name', limit_page_length=1)[0]
confirmed_purchase = frappe.get_all('Purchase Invoice', filters={'cc_center': center, 'docstatus': 1, 'name': ['not like', 'CC9-%']}, pluck='name', limit_page_length=1)[0]

print(json.dumps({
    "center": center,
    "price_list": price_list,
    "manager": manager_email,
    "secretary": sec_email,
    "pro_a": pro_a_email,
    "pro_a_name": pro_a_name,
    "confirmed_invoice": confirmed_invoice,
    "cancelled_invoice": cancelled_invoice,
    "confirmed_purchase": confirmed_purchase
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

  async function checkPrint(page, viewport, kind) {
    const preview = page.locator('iframe.document-preview');
    await preview.waitFor();
    const html = await preview.getAttribute('srcdoc');
    assert.ok(html.includes('Righe del documento') && html.includes('Importi'));
    const metrics = await preview.evaluate(frame => {
      const d = frame.contentDocument, table = d.querySelector('table.lines');
      const root = d.documentElement, cells = [...table.querySelectorAll('thead th')];
      const clip = frame.parentElement;
      return { frame: frame.clientWidth, document: root.clientWidth, scroll: root.scrollWidth,
        headers: cells.length, right: Math.max(...cells.map(c => c.getBoundingClientRect().right)),
        outerWidth: clip.clientWidth, outerScroll: clip.scrollWidth };
    });
    assert.strictEqual(metrics.headers, 6);
    assert.ok(metrics.frame >= 790 && metrics.scroll <= metrics.document + 1 && metrics.right <= metrics.document + 1,
      `${kind} ${viewport}: preview columns clipped: ${JSON.stringify(metrics)}`);
    if (viewport === 'mobile') {
      assert.ok(metrics.outerScroll > metrics.outerWidth, 'Mobile preview must be horizontally scrollable');
      await page.locator('.document-preview-scroll').evaluate(el => { el.scrollLeft = el.scrollWidth; });
      assert.ok(await page.locator('.document-preview-scroll').evaluate(el => el.scrollLeft > 0), 'Mobile scroll failed');
    }
    await saveShot(page, `audit09-a4-preview-${kind}-${viewport}.png`);
    const printPage = await browser.newPage({ viewport: { width: 688, height: 1000 } });
    try {
      await printPage.setContent(html, { waitUntil: 'load' });
      await printPage.emulateMedia({ media: 'print' });
      const layout = await printPage.locator('table.lines').evaluate(table => {
        const r = table.getBoundingClientRect(); return { right: r.right, width: document.documentElement.clientWidth, headers: table.querySelectorAll('th').length };
      });
      assert.strictEqual(layout.headers, 6); assert.ok(layout.right <= layout.width + 1, 'A4 print table overflows');
      const pdf = await printPage.pdf({ format: 'A4', printBackground: true, preferCSSPageSize: true });
      assert.ok(pdf.subarray(0, 5).toString() === '%PDF-');
      const box = pdf.toString('latin1').match(/\/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]/);
      assert.ok(box && Math.abs(Number(box[1]) - 595) < 2 && Math.abs(Number(box[2]) - 842) < 2, 'PDF page is not A4');
      fs.writeFileSync(path.join(ARTIFACT_DIR, `audit09-a4-${kind}-${viewport}.pdf`), pdf);
      // Stress the same server-rendered template with repeated synthetic rows;
      // this exercises pagination without changing any Frappe document.
      await printPage.locator('table.lines tbody').evaluate(body => {
        const first = body.querySelector('tr'); for (let i = 0; i < 80; i++) body.append(first.cloneNode(true));
      });
      const multi = await printPage.pdf({ format: 'A4', printBackground: true, preferCSSPageSize: true });
      const pages = (multi.toString('latin1').match(/\/Type\s*\/Page\b/g) || []).length;
      assert.ok(pages > 1, `Expected multipage PDF, got ${pages}`);
      fs.writeFileSync(path.join(ARTIFACT_DIR, `audit09-a4-${kind}-${viewport}-multipage.pdf`), multi);
      console.log('[PRINT-UAT]', kind, viewport, JSON.stringify(metrics), 'multipage PDF pages', pages);
    } finally { await printPage.close(); }
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
        await page.locator('.drawer[role="dialog"] .property-list').first().waitFor({ state: 'visible', timeout: 10000 });
        assert.ok(await page.locator('.drawer[role="dialog"] .property-list dt').count() > 0, `${label}: empty detail`);
        await saveShot(page, `audit09-${slug}-detail-${viewport}.png`);
        await page.locator('.drawer[role="dialog"] button[aria-label="Chiudi"]').click();
      }
      // Change and restore only synthetic clone records. Compare the canonical ID
      // and the saved field through the real detail and mutation HTTP responses.
      for (const [label, fieldLabel, field, detailMethod, saveMethod] of [
        ['Pazienti', 'Nome', 'first_name', 'operations.profiles.patient_detail', 'operations.profiles.patient_save'],
        ['Professionisti', 'Nome', 'first_name', 'operations.profiles.practitioner_detail', 'operations.profiles.practitioner_save'],
        ['Articoli', 'Articolo', 'item_name', 'catalog.detail', 'catalog.item_save'],
        ['Modelli pacchetto', 'Modello', 'title', 'catalog.detail', 'catalog.package_template_save']
      ]) {
        await page.locator(`.archive-menu button[aria-label="${label}"]`).click();
        await waitForList(page, label);
        const detailResponse = page.waitForResponse(r => r.url().includes(detailMethod) && r.ok());
        await page.locator('.archive-panel tbody tr').first().click();
        const original = (await (await detailResponse).json()).message;
        const drawer = page.locator('.drawer[role="dialog"]');
        await drawer.getByRole('button', { name: 'Modifica scheda' }).click();
        const change = async value => {
          const form = page.getByRole('dialog', { name: /Modifica/ });
          await form.getByLabel(fieldLabel).first().fill(value);
          await form.getByLabel('Motivo della modifica').fill('Prova sintetica reversibile');
          await form.getByRole('button', { name: 'Rivedi modifica' }).click();
          const save = page.waitForResponse(r => r.url().includes(saveMethod) && r.request().method() === 'POST');
          const updated = page.waitForResponse(r => r.url().includes(detailMethod) && new URL(r.url()).searchParams.get('name') === original.name && r.ok());
          await page.getByRole('button', { name: 'Conferma salvataggio' }).click();
          const response = await save;
          assert.ok(response.ok(), `${label}: HTTP ${response.status()}`);
          const posted = response.request().postDataJSON();
          assert.strictEqual(posted.name, original.name, `${label}: wrong canonical record`);
          assert.strictEqual(posted[field], value, `${label}: wrong value`);
          assert.strictEqual((await (await updated).json()).message[field], value, `${label}: saved field differs`);
          await page.getByText('Scheda salvata con successo.').waitFor();
        };
        const changed = `Prova reversibile ${viewport} ${label}`;
        await change(changed);
        assert.ok((await drawer.innerText()).includes(changed), `${label}: saved name missing`);
        await saveShot(page, `audit09-final-edit-${label.toLowerCase().replaceAll(' ', '-')}-${viewport}.png`);
        await drawer.getByRole('button', { name: 'Modifica scheda' }).click();
        await change(String(original[field]));
        const verify = await page.evaluate(async ({ method, center, name, kind }) => {
          const args = new URLSearchParams({ center, name }); if (kind) args.set('kind', kind);
          const r = await fetch('/api/method/centrochange_core.' + method + '?' + args);
          if (!r.ok) throw new Error('Detail verification failed'); return (await r.json()).message;
        }, { method: detailMethod, center: env.center, name: original.name, kind: label === 'Articoli' ? 'Item' : label === 'Modelli pacchetto' ? 'CC Package Template' : '' });
        assert.strictEqual(verify[field], original[field], `${label}: restoration failed`);
        for (const [key, value] of Object.entries(original)) {
          if (key !== 'modified') assert.deepStrictEqual(verify[key], value, `${label}: field ${key} changed after restoration`);
        }
        await drawer.getByRole('button', { name: 'Chiudi' }).click();
      }
      await page.locator('.archive-menu button[aria-label="Fatture pazienti"]').click();
      for (const [id, cancelled] of [[env.confirmed_invoice, false], [env.cancelled_invoice, true]]) {
        const search = page.getByRole('searchbox', { name: 'Cerca in fatture pazienti' });
        await search.fill(id);
        await page.locator('.archive-panel tbody tr').first().waitFor({ state: 'visible', timeout: 15000 });
        const response = page.waitForResponse(r => r.url().includes('finance.documents.detail') && new URL(r.url()).searchParams.get('name') === id);
        await page.locator('.archive-panel tbody tr').first().click();
        const document = (await (await response).json()).message;
        assert.strictEqual(document.name, id);
        const listParty = (await page.locator('.archive-panel tbody tr').first().locator('td').nth(1).innerText()).trim();
        assert.strictEqual(listParty, document.party || '—', 'Elenco e documento hanno soggetti diversi');
        const drawer = page.locator('.drawer[role="dialog"]');
        await drawer.getByRole('heading', { name: 'Documento completo' }).waitFor();
        if (document.party) assert.strictEqual(await drawer.getByText(document.party, { exact: true }).count(), 2, 'Riepilogo e documento hanno soggetti diversi');
        await drawer.getByRole('heading', { name: 'Servizi e articoli' }).waitFor();
        assert.ok((await drawer.innerText()).includes(id), 'Numero documento assente dal dettaglio');
        if (cancelled) {
          assert.strictEqual(await drawer.getByRole('button', { name: 'Anteprima e stampa' }).count(), 0);
          assert.ok((await drawer.innerText()).includes('non è un importo da incassare'));
        } else {
          await drawer.getByRole('button', { name: 'Anteprima e stampa' }).click();
          await checkPrint(page, viewport, 'sales');
          await page.getByRole('dialog', { name: /Anteprima/ }).getByRole('button', { name: 'Chiudi' }).first().click();
        }
        await saveShot(page, `audit09-final-${cancelled ? 'cancelled' : 'confirmed'}-${viewport}.png`);
        await drawer.getByRole('button', { name: 'Chiudi' }).click();
      }
      await page.locator('.archive-menu button[aria-label="Fatture professionisti"]').click();
      await page.locator('.archive-panel input[type="search"]').fill(env.confirmed_purchase);
      await page.locator('.archive-panel tbody tr').first().waitFor({ state: 'visible', timeout: 15000 });
      const purchaseResponse = page.waitForResponse(r => r.url().includes('finance.documents.detail') && new URL(r.url()).searchParams.get('name') === env.confirmed_purchase);
      await page.locator('.archive-panel tbody tr').first().click();
      assert.strictEqual((await (await purchaseResponse).json()).message.name, env.confirmed_purchase);
      const purchaseDrawer = page.locator('.drawer[role="dialog"]');
      await purchaseDrawer.getByRole('button', { name: 'Anteprima e stampa' }).click();
      await checkPrint(page, viewport, 'purchase');
      await page.getByRole('dialog', { name: /Anteprima/ }).getByRole('button', { name: 'Chiudi' }).first().click();
      await purchaseDrawer.getByRole('button', { name: 'Chiudi' }).click();
      for (const area of ['Agenda', 'Report', 'Finanza']) {
        const menu = page.getByRole('button', { name: 'Apri menu' });
        if (await menu.isVisible()) await menu.click();
        await page.locator('.sidebar').getByRole('button', { name: area, exact: true }).click();
        await page.getByRole('heading', { name: area, exact: true }).waitFor({ state: 'visible' });
        await page.waitForTimeout(500);
        assert.strictEqual(await page.locator('main [role="alert"]').count(), 0, `${area}: error`);
        await saveShot(page, `audit09-final-smoke-${area.toLowerCase()}-${viewport}.png`);
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
