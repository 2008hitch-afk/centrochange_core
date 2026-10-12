// Isolated browser reconciliation of patient and professional Desk projections.
const {chromium} = require('playwright');
const fs = require('fs');
const assert = require('assert');
const demo = JSON.parse(fs.readFileSync('/qa-fixture.json'));
const fixture = demo.fixture;

(async () => {
  const browser = await chromium.launch({headless:true,args:[
    '--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server',
    '--no-first-run','--disable-background-networking','--disable-component-update',
    '--disable-default-apps','--disable-sync','--disable-extensions',
    '--disk-cache-size=0','--media-cache-size=0']});
  try {
    const page=await browser.newPage({viewport:{width:1440,height:900},locale:'it-IT'});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    const base='http://centrochange.local:8080';
    const common={center:fixture.centers[0],start:'2026-09-28',end:'2026-10-31'};
    const patientRoute='/app/cc-unified-desk?'+new URLSearchParams({cc_view:'patient',...common,patient:demo.patients.Theta});
    await page.goto(base+'/login?redirect-to='+encodeURIComponent(patientRoute));
    await page.locator('#login_email').fill(fixture.users.m.name);
    await page.locator('#login_password').fill(fixture.users.m.password);
    await page.locator('.form-login button[type="submit"]').click();
    await page.locator('#invoiced summary').waitFor({timeout:60000});
    const patient=await page.evaluate(() => ({
      period:document.querySelector('#patient-period')?.textContent,
      invoiced:document.querySelector('#invoiced summary')?.textContent,
      open:document.querySelector('#outstanding summary')?.textContent,
      overdue:document.querySelector('#overdue summary')?.textContent,
      error:document.querySelector('#patient-error')?.textContent,
      body:document.querySelector('#patient-content')?.innerText.slice(0,1000)
    }));
    assert(patient.period.includes('28/09/2026')&&patient.period.includes('31/10/2026'));
    assert(patient.invoiced.includes('1 record')&&patient.open.includes('1 record')&&patient.overdue.includes('1 record'));
    assert(!patient.error&&patient.body.includes('100,00'));
    await page.locator('#invoiced summary').click();
    assert.strictEqual(await page.locator('#invoiced tr').count(),2);
    await page.screenshot({path:'/qa-results/r9-patient-report-synthetic.png',fullPage:false});
    const professionalRoute='/app/cc-unified-desk?'+new URLSearchParams({cc_view:'professional',...common,practitioner:fixture.practitioners[0]});
    await page.goto(base+professionalRoute);
    await page.locator('#sessions summary').waitFor({timeout:60000});
    const professional=await page.evaluate(() => ({
      period:document.querySelector('#professional-period')?.textContent,
      summary:document.querySelector('#sessions summary')?.textContent,
      records:document.querySelectorAll('#sessions tbody tr.professional-session').length,
      error:document.querySelector('#professional-error')?.textContent,
      overflow:document.documentElement.scrollWidth>innerWidth
    }));
    assert(professional.period.includes('28/09/2026')&&professional.period.includes('31/10/2026'));
    assert(!professional.error&&!professional.overflow);
    assert(professional.summary.includes(`${professional.records} record`));
    await page.screenshot({path:'/qa-results/r9-professional-report-synthetic.png',fullPage:false});
    assert.deepStrictEqual(errors,[]);
    console.log(JSON.stringify({status:'PASS',patient:{period:patient.period,invoiced:patient.invoiced,open:patient.open,overdue:patient.overdue},professional,errors:0}));
  } finally {await browser.close();}
})().catch(error=>{console.error(error.stack||error.message);process.exit(1);});
