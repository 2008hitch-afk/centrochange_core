/* Full isolated browser rehearsal. Runs only in the disposable CI clone. */
const { chromium } = require('playwright')
const { execFileSync } = require('child_process')
const crypto = require('crypto')
const fs = require('fs')
const path = require('path')
const assert = require('assert')
const out = process.env.CC_ARTIFACT_DIR
fs.mkdirSync(out, { recursive: true })
const base = 'http://centrochange.local:8099'
function py(code, data = {}) {
  return execFileSync('docker', ['exec', '-i', '-e', 'FRAPPE_STREAM_LOGGING=1', '-w', '/home/frappe/frappe-bench', 'cc183-clone-backend', 'env/bin/python', '-c', code], { input: JSON.stringify(data), encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).trim()
}
const discover = `import frappe,json,sys
from centrochange_core.uat.demo import read
frappe.init('centrochange.local',sites_path='sites');frappe.connect()
try:
 assert frappe.conf.get('cc_synthetic_dev')==1 and frappe.conf.get('cc_uat_demo')==1
 f=read()['fixture'];print(json.dumps({'manager':f['users']['m'],'professional':f['users']['a'],'patients':f['patients'],'a':f['centers'][0],'b':f['centers'][1]}))
finally:frappe.destroy()`
const initInactive = `import frappe,json,sys
from centrochange_core.security.center_state import set_operational
from centrochange_core.uat.demo import read
d=json.load(sys.stdin);frappe.init('centrochange.local',sites_path='sites');frappe.connect()
try:
 assert frappe.conf.get('cc_synthetic_dev')==1 and frappe.conf.get('cc_uat_demo')==1
 f=read()['fixture'];assert d['center']==f['centers'][1] and d['manager']==f['users']['m']['name']
 frappe.set_user(d['manager']);set_operational(d['center'],0,'AUDIT10-HARNESS synthetic inactive center');frappe.db.commit();print('PASS')
finally:frappe.destroy()`
const setup = `import json,sys,frappe
from frappe.utils.password import update_password
from centrochange_core.uat.demo import read
d=json.load(sys.stdin);frappe.init('centrochange.local',sites_path='sites');frappe.connect()
try:
 assert frappe.conf.get('cc_synthetic_dev')==1 and frappe.conf.get('cc_uat_demo')==1
 assert d['user'].startswith('audit10-test-') and d['user'].endswith('@example.invalid') and not frappe.db.exists('User',d['user'])
 frappe.set_user('Administrator');frappe.in_test=True
 frappe.get_doc({'doctype':'User','email':d['user'],'first_name':d['tag'],'enabled':1,'send_welcome_email':0,'roles':[{'role':'CC Professional'}]}).insert(ignore_permissions=True)
 update_password(d['user'],d['password']);contacts=frappe.get_all('Contact',filters={'user':d['user']},pluck='name',limit_page_length=0);assert contacts
 f=read()['fixture'];assert f['centers'][0]==d['center'] and frappe.db.get_value('Branch',d['center'],'cc_operational')==1
 frappe.db.commit();print(json.dumps({'contacts':contacts}))
except:frappe.db.rollback();raise
finally:frappe.destroy()`
const cleanup = `import json,sys,frappe
from centrochange_core.security.audit import internal_write
from frappe.sessions import clear_sessions
d=json.load(sys.stdin);frappe.init('centrochange.local',sites_path='sites');frappe.connect()
try:
 assert frappe.conf.get('cc_synthetic_dev')==1 and d['user'].startswith('audit10-test-') and d['user'].endswith('@example.invalid')
 frappe.set_user('Administrator');frappe.in_test=True;contacts=[]
 if frappe.db.exists('User',d['user']):
  assert frappe.db.get_value('User',d['user'],'first_name')==d['tag']
  members=frappe.get_all('CC Center Membership',filters={'user':d['user']},fields=['name','center'],limit_page_length=0);assert len(members)<=1 and all(x.center==d['center'] for x in members)
  contacts=frappe.get_all('Contact',filters={'user':d['user']},pluck='name',limit_page_length=0)
  for c in contacts:assert frappe.db.get_value('Contact',c,'first_name')==d['tag']
  clear_sessions(user=d['user'],force=True)
  for m in members:
   with internal_write('cc_permission_write'):frappe.delete_doc('CC Center Membership',m.name,ignore_permissions=True,force=True)
  frappe.delete_doc('User',d['user'],ignore_permissions=True,force=True)
  for c in contacts:frappe.delete_doc('Contact',c,ignore_permissions=True,force=True)
  frappe.db.delete('DefaultValue',{'parent':d['user']});frappe.db.commit()
 assert not frappe.db.exists('User',d['user']) and not frappe.db.count('CC Center Membership',{'user':d['user']})
 for dt,filters in [('Has Role',{'parent':d['user']}),('User Permission',{'user':d['user']}),('DocShare',{'user':d['user']}),('Sessions',{'user':d['user']}),('DefaultValue',{'parent':d['user']}),('__Auth',{'doctype':'User','name':d['user']})]:assert not frappe.db.count(dt,filters),dt
 assert not frappe.db.exists('Notification Settings',d['user']) and all(not frappe.db.exists('Contact',x) for x in contacts)
 events=frappe.get_all('CC Audit Event',filters={'reason':d['tag']},fields=['name','event_type'],limit_page_length=0)
 history={'comments':frappe.db.count('Comment',{'subject':['like','%'+d['user']+'%']}),'deleted_documents':frappe.db.count('Deleted Document',{'deleted_name':['like','%'+d['user']+'%']}),'permission_logs':frappe.db.count('Permission Log',{'for_document':d['user']})}
 print(json.dumps({'status':'PASS','retained_test_audit':len(events),'event_names':[x.name for x in events],'contacts_removed':len(contacts),'retained_system_history':history}))
except:frappe.db.rollback();raise
finally:frappe.destroy()`
const cfg = JSON.parse(py(discover))
assert.strictEqual(py(initInactive, { center: cfg.b, manager: cfg.manager.name }), 'PASS')
async function login(page, user, password) {
  await page.goto(base + '/login?redirect-to=/premium', { waitUntil: 'domcontentloaded' })
  await page.locator('#login_email').fill(user)
  await page.locator('#login_password').fill(password)
  await page.locator('.form-login button[type=submit]').click()
  await page.waitForURL(url => url.pathname === '/premium', { timeout: 30000 })
  const identity = await page.evaluate(async () => { const r = await fetch('/api/method/frappe.auth.get_logged_user'); return { status: r.status, body: await r.json() } })
  assert.strictEqual(identity.status, 200)
  assert.strictEqual(identity.body.message, user)
  await page.getByRole('heading', { name: 'Agenda', exact: true }).waitFor()
}
async function diagnose(page, label, stage, error, faults) {
  let pathname = 'unavailable'
  try { pathname = new URL(page.url()).pathname } catch {}
  const kind = faults.some(x => x.status >= 500 || x.type === 'pageerror' || x.type === 'unexpected_status') ? 'APP_FAILURE' : stage === 'authentication' ? 'AUTH_FAILURE' : 'HARNESS_FAILURE'
  const data = { classification: kind, stage, pathname, message: String(error.message).split('\n')[0], network: faults }
  fs.writeFileSync(path.join(out, label + '-failure.json'), JSON.stringify(data, null, 2))
  try { await page.screenshot({ path: path.join(out, label + '-failure.png'), mask: [page.locator('input'), page.locator('textarea'), page.locator('tbody'), page.locator('[role=dialog]')] }) } catch {}
  console.error(kind, stage, pathname)
}
async function round(browser, width, iteration) {
  const id = crypto.randomBytes(8).toString('hex'), user = `audit10-test-${id}@example.invalid`, tag = `AUDIT10-TEST-${id}`, password = crypto.randomBytes(24).toString('base64url')
  const label = `repeat-${width}-${iteration}`, inventory = path.join(out, label + '-inventory.json')
  fs.writeFileSync(inventory, JSON.stringify({ tag, status: 'PLANNED' }))
  let managerCtx, proCtx, page, stage = 'setup', failure, completed = false
  const faults = []
  try {
    py(setup, { user, tag, password, center: cfg.a })
    managerCtx = await browser.newContext({ viewport: { width, height: 900 }, locale: 'it-IT' })
    page = await managerCtx.newPage()
    page.on('pageerror', () => faults.push({ type: 'pageerror', status: 0 }))
    page.on('response', r => { if (r.status() >= 500) faults.push({ type: 'http', status: r.status(), path: new URL(r.url()).pathname.startsWith('/api/method/') ? new URL(r.url()).pathname : '/redacted' }) })
    stage = 'authentication'; await login(page, cfg.manager.name, cfg.manager.password)
    stage = 'access-ui'; await page.goto(base + '/premium#Gestione%20accessi', { waitUntil: 'networkidle' })
    await page.getByRole('heading', { name: 'Gestione accessi', exact: true }).waitFor()
    const center = page.locator('.center-selector select'); if (await center.count()) await center.selectOption(cfg.a)
    await page.getByRole('heading', { name: 'Gestione accessi', exact: true }).waitFor()
    let proPage
    for (const active of ['1', '0', '1']) {
      await page.getByRole('button', { name: 'Appartenenza', exact: true }).click()
      const d = page.getByRole('dialog', { name: 'Appartenenza al centro', exact: true })
      await d.getByLabel('Utente').selectOption(user); await d.getByLabel('Nuovo stato').selectOption(active)
      await d.getByLabel('Motivo della modifica').fill(tag); await d.getByRole('button', { name: 'Rivedi modifica', exact: true }).click()
      const response = page.waitForResponse(r => r.url().includes('security.lifecycle.set_membership') && r.request().method() === 'POST')
      await d.getByRole('button', { name: 'Conferma modifica', exact: true }).click(); const saved = await response; if (!saved.ok()) faults.push({ type: 'unexpected_status', status: saved.status(), path: '/api/method/security.lifecycle.set_membership' }); assert(saved.ok()); await d.waitFor({ state: 'hidden' })
      if (!proCtx) { stage = 'authentication'; proCtx = await browser.newContext({ viewport: { width, height: 900 }, locale: 'it-IT' }); proPage = await proCtx.newPage(); await login(proPage, user, password); stage = 'session-scope' }
      const status = await proPage.evaluate(async c => (await fetch('/api/method/centrochange_core.operations.workspace.patient_search?center=' + encodeURIComponent(c) + '&query=')).status, cfg.a)
      if (status !== (active === '0' ? 403 : 200)) faults.push({ type: 'unexpected_status', status, path: '/api/method/operations.workspace.patient_search' })
      assert.strictEqual(status, active === '0' ? 403 : 200)
    }
    stage = 'security-and-audit'
    const negative = await page.evaluate(async ({ user, center, tag }) => { const token = document.querySelector('meta[name="csrf-token"]').content; return (await fetch('/api/method/centrochange_core.security.lifecycle.set_membership', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': token }, body: new URLSearchParams({ user, center, active: '1', reason: tag }) })).status }, { user, center: cfg.b, tag })
    if (negative !== 403) faults.push({ type: 'unexpected_status', status: negative, path: '/api/method/security.lifecycle.set_membership' })
    assert.strictEqual(negative, 403)
    const proDenied = await proPage.evaluate(async () => (await fetch('/api/method/centrochange_core.security.audit_view.events?start=2026-01-01&end=2026-12-31')).status)
    assert.strictEqual(proDenied, 403)
    await page.goto(base + '/premium#Registro%20modifiche', { waitUntil: 'networkidle' }); await page.getByRole('heading', { name: 'Registro modifiche', exact: true }).waitFor()
    const row = page.getByRole('row', { name: new RegExp(tag) }).first(); await row.waitFor(); await row.focus(); await row.press('Enter')
    const detail = page.getByRole('dialog', { name: 'Appartenenza al centro', exact: true }); await detail.waitFor()
    assert((await detail.innerText()).includes('Prima:') && (await detail.innerText()).includes('Dopo:'))
    await page.screenshot({ path: path.join(out, label + '-audit.png'), mask: [page.locator('tbody'), detail] })
    stage = 'professional-patients'
    const existing = await browser.newContext({ viewport: { width, height: 900 }, locale: 'it-IT' }); const patientPage = await existing.newPage()
    try {
      await login(patientPage, cfg.professional.name, cfg.professional.password)
      await patientPage.goto(base + '/premium#Pazienti', { waitUntil: 'networkidle' })
      await patientPage.getByRole('heading', { name: 'Pazienti', exact: true }).waitFor()
      const scopes = await patientPage.evaluate(async ({ center, other }) => { const get = async c => { const r = await fetch('/api/method/centrochange_core.operations.workspace.patient_search?center=' + encodeURIComponent(c) + '&query='); return { status: r.status, body: await r.json() } }; return [await get(center), await get(other)] }, { center: cfg.a, other: cfg.b })
      assert.strictEqual(scopes[0].status, 200); assert.strictEqual(scopes[1].status, 403)
      const ids = scopes[0].body.message.patients.map(x => x.name); assert(ids.includes(cfg.patients[0])); assert(!ids.includes(cfg.patients[1]))
      await patientPage.screenshot({ path: path.join(out, label + '-patients.png'), mask: [patientPage.locator('tbody')] })
    } finally { await existing.close() }
    assert(!faults.length, 'Unexpected browser/server errors')
    completed = true
  } catch (error) { failure = error; if (page) await diagnose(page, label, stage, error, faults); else console.error('HARNESS_FAILURE', stage) }
  finally {
    if (proCtx) await proCtx.close(); if (managerCtx) await managerCtx.close()
    try {
      const result = JSON.parse(py(cleanup, { user, tag, center: cfg.a }))
      fs.writeFileSync(inventory, JSON.stringify({ user, tag, status: result.status, retained_test_audit: result.retained_test_audit, event_names: result.event_names, contacts_removed: result.contacts_removed, retained_system_history: result.retained_system_history }))
      if (completed) assert.strictEqual(result.retained_test_audit, 3)
      console.log('AUDIT10_FIXTURE_CLEANUP', label, result.status, 'retained_test_audit=' + result.retained_test_audit)
    } catch (error) { console.error('HARNESS_FAILURE fixture-cleanup'); failure = failure || error }
  }
  if (failure) throw failure
  console.log('AUDIT10_FULL_REHEARSAL_PASS', label)
}
;(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--host-resolver-rules=MAP centrochange.local 127.0.0.1', '--no-proxy-server'] })
  try { for (const width of [1440, 390]) for (const iteration of [1, 2]) await round(browser, width, iteration) }
  finally { await browser.close() }
})().catch(error => { console.error(String(error.message).split('\n')[0]); process.exit(1) })
