/* One synthetic POS payment on the existing DEV. The host owns native reversal. */
const fs = require('fs');
const assert = require('assert');
const { chromium } = require('/tmp/cc-browser-qa/node_modules/playwright');

const fixture = JSON.parse(fs.readFileSync(process.env.CC_DEMO_CREDENTIALS, 'utf8'));
const invoice = process.env.CC_POS_INVOICE;
const mode = process.env.CC_POS_MODE;
const resultPath = process.env.CC_POS_RESULT;
const base = 'http://centrochange.local:8082';
const browserPath = process.env.CC_CHROMIUM;
assert(invoice && mode && resultPath && browserPath);

async function login(page, role, destination) {
  await page.goto(`${base}/login?redirect-to=${destination}`);
  await page.locator('#login_email').fill(fixture.users[role].name);
  await page.locator('#login_password').fill(fixture.users[role].password);
  await page.locator('.form-login button[type="submit"]').click();
  await page.waitForURL(`**${destination}`);
}

(async () => {
  const browser = await chromium.launch({headless: true, executablePath: browserPath,
    args: ['--host-resolver-rules=MAP centrochange.local 127.0.0.1', '--no-proxy-server']});
  try {
    const context = await browser.newContext({viewport: {width: 1440, height: 900},
      locale: 'it-IT', timezoneId: 'Europe/Rome'});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await login(page, 'f', '/finanza');
    await page.locator('#finance-content').getByText('Contabilità del centro').waitFor();
    await page.getByRole('button', {name: 'Fatture pazienti', exact: true}).click();
    const row = page.locator(`#finance-content tr[data-name="${invoice}"]`);
    await row.waitFor();
    await row.click();
    await page.getByRole('button', {name: 'Registra pagamento', exact: true}).waitFor();
    const before = await page.locator('#detail').innerText();
    assert(before.includes(invoice) && before.includes('Residuo'));
    await page.screenshot({path: process.env.CC_POS_EVIDENCE + '/before.png', fullPage: true});
    await page.getByRole('button', {name: 'Registra pagamento', exact: true}).click();
    await page.locator('#modal [name=amount]').fill('5');
    await page.locator('#modal [name=mode_of_payment]').selectOption(mode);
    await page.locator('#modal [name=reason]').fill(process.env.CC_POS_TEST_TAG + ' prova POS sintetica');
    const reply = page.waitForResponse(response => response.url().includes('finance.receivables.pay') &&
      response.request().method() === 'POST');
    await page.locator('#modal-submit').click();
    const response = await reply;
    assert(response.ok(), `POS API HTTP ${response.status()}`);
    const payment = (await response.json()).message;
    assert(payment.payment && Math.abs(Number(payment.invoice.outstanding) -
      (Number(payment.invoice.total) - 5)) < 0.011);
    fs.writeFileSync(resultPath, JSON.stringify({payment: payment.payment, invoice}), {mode: 0o600});
    await page.reload();
    await page.getByRole('button', {name: 'Fatture pazienti', exact: true}).click();
    await row.waitFor();
    await row.click();
    assert((await page.locator('#detail').innerText()).includes(invoice));
    await page.screenshot({path: process.env.CC_POS_EVIDENCE + '/after-refresh.png', fullPage: true});
    await page.locator('#logout').click();
    await login(page, 'a', '/centrochange');
    const denied = await page.evaluate(async name => (await fetch(
      '/api/method/centrochange_core.finance.receivables.position?name=' + encodeURIComponent(name))).status,
      invoice);
    assert(denied === 403, `Professional direct invoice API returned ${denied}`);
    assert.deepStrictEqual(errors, []);
    console.log('CC_POS_BROWSER=' + JSON.stringify({status: 'PASS', payment: payment.payment,
      browser_reload: true, professional_denied: true, js_errors: 0}));
  } finally {
    await browser.close();
  }
})().catch(error => {console.error('CC_POS_BROWSER_FAIL=' + error.message); process.exitCode = 1;});
