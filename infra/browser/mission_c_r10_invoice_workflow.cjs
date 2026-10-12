// Mutating R10 probe: isolated C109 synthetic clone ONLY, after checkpoint.
// Uses a different unbilled Alfa session; never rewrites the historically paid
// invoice referenced by the original demo manifest. Run once per clone.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const demo = JSON.parse(fs.readFileSync('/qa-fixture.json', 'utf8'));
const target = 'http://centrochange.local:8080';
const source = demo.appointments['Alfa non incassata 2'];
assert(source && demo.invoices['Alfa bozza'] && demo.fixture.users.m);

(async () => {
  const browser = await chromium.launch({headless:true,args:[
    '--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server',
    '--no-first-run','--disable-background-networking','--disable-component-update',
    '--disable-default-apps','--disable-sync','--disable-extensions',
    '--disk-cache-size=0','--media-cache-size=0']});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:900},locale:'it-IT'});
    const errors=[]; page.on('pageerror',e=>errors.push(e.message));
    await page.goto(target+'/login?redirect-to='+encodeURIComponent('/app/cc-unified-desk?cc_view=finance'));
    await page.locator('#login_email').fill(demo.fixture.users.m.name);
    await page.locator('#login_password').fill(demo.fixture.users.m.password);
    await page.locator('.form-login button[type="submit"]').click();
    await page.locator('#finance-content').waitFor({timeout:60000});
    await page.locator('#center').selectOption(demo.fixture.centers[0]);
    await page.locator('#navigation [data-view="Fatture pazienti"]').click();
    await page.locator('#finance-action').click();
    const candidates = page.locator('#modal [name="sources"]');
    await candidates.waitFor();
    const values = await candidates.locator('option').evaluateAll(nodes=>nodes.map(n=>n.value));
    assert(values.includes(source), 'independent Alfa session is not unbilled: stop; never reuse paid draft');
    await candidates.selectOption(source);
    await page.locator('#modal [name="posting_date"]').fill('2026-10-05');
    await page.locator('#modal [name="due_date"]').fill('2026-10-31');
    await page.locator('#modal [name="reason"]').fill('C109 R10 synthetic independent Alfa invoice');
    const drafted=page.waitForResponse(r=>r.url().includes('finance.receivables.draft')&&r.request().method()==='POST');
    await page.locator('#modal-submit').click();
    const draftResponse=await drafted; assert.equal(draftResponse.status(),200);
    const invoice=(await draftResponse.json()).message;
    assert(invoice?.name && invoice.docstatus===0);
    assert.notEqual(invoice.name,demo.invoices['Alfa bozza']);
    await page.locator(`#finance-content tr[data-name="${invoice.name}"]`).click();
    await page.locator('#post-invoice').click();
    await page.locator('#modal [name="reason"]').fill('C109 R10 synthetic approval');
    const submitted=page.waitForResponse(r=>r.url().includes('finance.receivables.submit')&&r.request().method()==='POST');
    await page.locator('#modal-submit').click();
    const submitResponse=await submitted;assert.equal(submitResponse.status(),200);
    assert.equal((await submitResponse.json()).message.docstatus,1);
    await page.locator(`#finance-content tr[data-name="${invoice.name}"]`).click();
    await page.locator('#pay-invoice').click();
    await page.locator('#modal [name="reason"]').fill('C109 R10 synthetic payment');
    const paid=page.waitForResponse(r=>r.url().includes('finance.receivables.pay')&&r.request().method()==='POST');
    await page.locator('#modal-submit').click();
    const payResponse=await paid;assert.equal(payResponse.status(),200);
    const payment=(await payResponse.json()).message;
    assert(payment?.payment && payment?.invoice?.outstanding===0, 'native Payment Entry or settlement missing');
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({status:'PASS',invoice:invoice.name,source,
      checks:['draft_browser','submit_browser','payment_browser','canonical_response']}));
  } finally { await browser.close(); }
})().catch(error=>{console.error(error.stack||error.message);process.exit(1);});
