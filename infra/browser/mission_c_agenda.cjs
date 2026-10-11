// Read-only browser exercise of the versioned C109 Desk Agenda on synthetic data.
const {chromium} = require('playwright');
const fs = require('fs');
const fixture = JSON.parse(fs.readFileSync('/qa-fixture.json')).fixture;
const role = process.env.ROLE;
if (!['m','s','a','b','c'].includes(role)) throw new Error('Unsupported synthetic role');
const base = 'http://centrochange.local:8080';

(async () => {
  const browser = await chromium.launch({headless:true, timeout:90000,
    args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server',
      '--no-first-run','--disable-background-networking','--disable-component-update',
      '--disable-default-apps','--disable-sync','--disable-extensions',
      '--disk-cache-size=0','--media-cache-size=0']});
  const context = await browser.newContext({viewport:{width:1440,height:900},locale:'it-IT'});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  try {
    await page.goto(base+'/login?redirect-to='+encodeURIComponent('/app/cc-unified-desk?cc_view=agenda'));
    await page.locator('#login_email').fill(fixture.users[role].name);
    await page.locator('#login_password').fill(fixture.users[role].password);
    await page.locator('.form-login button[type="submit"]').click();
    await page.locator('#week-date').waitFor({timeout:60000});
    await page.locator('#week-date').evaluate(input => {
      input.value='2026-09-28';input.dispatchEvent(new Event('change',{bubbles:true}));
    });
    await page.waitForFunction(() => document.querySelector('#week-label')?.textContent.includes('28 set'),null,{timeout:30000});
    await page.waitForTimeout(1500);
    const before = await page.evaluate(() => ({
      center:document.querySelector('#center')?.selectedOptions[0]?.textContent?.trim(),
      week:document.querySelector('#week-label')?.textContent?.trim(),
      practitionerRows:document.querySelectorAll('.calendar-row').length,
      cards:[...document.querySelectorAll('.calendar-appointment')].map(card=>({
        appointment:card.dataset.name,
        date:card.closest('.calendar-cell')?.dataset.date,
        practitioner:card.closest('.calendar-cell')?.dataset.practitioner
      })),
      overflow:document.documentElement.scrollWidth>innerWidth,
      headers:document.querySelectorAll('.calendar-day-header').length
    }));
    let detail=false,history=false,notes=false,booking=false;
    if (before.cards.length) {
      await page.locator('.calendar-appointment').first().click();
      detail=await page.getByRole('tab',{name:'Seduta'}).isVisible();
      await page.getByRole('tab',{name:'Storico'}).click();
      history=await page.getByRole('tab',{name:'Storico'}).getAttribute('aria-selected')==='true';
      await page.getByRole('tab',{name:'Note'}).click();
      notes=await page.getByRole('tab',{name:'Note'}).getAttribute('aria-selected')==='true';
    }
    if (role==='s') await page.screenshot({path:'/qa-results/agenda-desktop-synthetic.png',fullPage:false});
    const book=page.locator('#new-booking');
    if (await book.isVisible()) {
      await book.click();
      booking=await page.locator('dialog#modal[open]').isVisible().catch(()=>false);
    }
    const result={role,...before,detail,history,notes,booking,errors};
    fs.writeFileSync('/qa-results/agenda-'+role+'.json',JSON.stringify(result,null,2));
    console.log(JSON.stringify({role,center:before.center,week:before.week,rows:before.practitionerRows,
      cards:before.cards.length,headers:before.headers,overflow:before.overflow,
      detail,history,notes,booking,errors:errors.length}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e.message);process.exit(1);});
