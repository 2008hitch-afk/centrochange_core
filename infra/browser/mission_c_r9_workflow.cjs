// Isolated synthetic Desk workflow. One Chromium process, no RC22 mutation.
const {chromium} = require('playwright');
const fs = require('fs');
const assert = require('assert');
const demo = JSON.parse(fs.readFileSync('/qa-fixture.json'));
const fixture = demo.fixture;
const browserArgs = ['--host-resolver-rules=MAP centrochange.local 127.0.0.1',
  '--no-proxy-server', '--no-first-run', '--disable-background-networking',
  '--disable-component-update', '--disable-default-apps', '--disable-sync',
  '--disable-extensions', '--disk-cache-size=0', '--media-cache-size=0'];

(async () => {
  const browser = await chromium.launch({headless:true,args:browserArgs});
  try {
    const context = await browser.newContext({viewport:{width:1440,height:900},locale:'it-IT',timezoneId:'Europe/Rome'});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const base = 'http://centrochange.local:8080';
    await page.goto(base+'/login?redirect-to='+encodeURIComponent('/app/cc-unified-desk?cc_view=agenda'));
    await page.locator('#login_email').fill(fixture.users.s.name);
    await page.locator('#login_password').fill(fixture.users.s.password);
    await page.locator('.form-login button[type="submit"]').click();
    await page.locator('#new-booking').waitFor({timeout:60000});
    await page.locator('#center').selectOption(fixture.centers[0]);
    await page.locator('#new-booking').click();
    async function choose(name,value) {
      const select = page.locator(`#modal select[name="${name}"]`);
      const input = select.locator('xpath=preceding-sibling::div[contains(@class,"cc-combobox")][1]//input');
      await input.fill(value);
      await page.locator('.cc-options:visible [role=option]').first().waitFor();
      await input.press('ArrowDown');
      await input.press('Enter');
      assert.strictEqual(await select.inputValue(),value);
    }
    await choose('patient',demo.patients.Gamma);
    await choose('practitioner',fixture.practitioners[0]);
    await page.locator('#modal [name=service]').selectOption(fixture.catalog['Appointment Type'][0]);
    await page.locator('#modal [name=date]').fill('2099-01-12');
    await page.locator('#modal [name=time]').fill('09:00');
    await page.locator('#modal [name=reason]').fill('C109-r9 synthetic Desk browser workflow');
    async function save(method) {
      const response = page.waitForResponse(r => r.url().includes(method) && r.request().method()==='POST');
      await page.locator('#modal-submit').click();
      const result = await response;
      if (!result.ok()) {
        const body = await result.json().catch(() => ({}));
        throw new Error(`${method} returned ${result.status()}: ${body._server_messages || body.message || body.exception || 'no detail'}`);
      }
      await page.locator('#modal[open]').waitFor({state:'hidden'});
      return (await result.json()).message;
    }
    const appointment = (await save('scheduling.booking.book')).name;
    await page.locator('#week-date').evaluate(input => {
      input.value='2099-01-12'; input.dispatchEvent(new Event('change',{bubbles:true}));
    });
    const card = page.locator(`.calendar-appointment[data-name="${appointment}"]`);
    await card.waitFor({timeout:30000});
    await card.click();
    await page.locator('#move-session').click();
    await page.locator('#modal [name=time]').fill('10:00');
    await page.locator('#modal [name=reason]').fill('C109-r9 synthetic reschedule');
    await save('scheduling.booking.reschedule');
    await card.waitFor({timeout:30000});
    assert((await card.innerText()).includes('10:00'));
    await card.click();
    await page.locator('#cancel-session').click();
    await page.locator('#modal [name=reason]').fill('C109-r9 synthetic cancellation');
    await save('operations.lifecycle.cancel');
    await card.waitFor({timeout:30000});
    assert((await card.innerText()).includes('Cancellata'));
    await page.setViewportSize({width:390,height:844});
    const mobileOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    await page.screenshot({path:'/qa-results/r9-workflow-mobile.png',fullPage:false});
    assert(!mobileOverflow,'mobile document overflow');
    assert.deepStrictEqual(errors,[]);
    console.log(JSON.stringify({status:'PASS',appointment,checks:['booking','reschedule','cancel','mobile_no_overflow'],errors:0}));
  } finally {await browser.close();}
})().catch(error => {console.error(error.stack || error.message);process.exit(1);});
