// Functional read-only detail probes. Uses current document IDs, no RC22 IDs.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const fixture = JSON.parse(fs.readFileSync(process.env.CC_AUDIT_FIXTURE, 'utf8'));
const output = process.env.CC_AUDIT_OUTPUT;
const base = 'http://centrochange.local:8082';
fs.mkdirSync(output, {recursive:true, mode:0o700});

(async () => {
  const browser = await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
  const results=[];
  try {
    for (const width of [1440,390]) {
      const context = await browser.newContext({viewport:{width,height:900},locale:'it-IT',timezoneId:'Europe/Rome',serviceWorkers:'block'});
      const page=await context.newPage(); const errors=[]; const writes=[];
      page.on('pageerror',e=>errors.push(e.message));
      page.on('request',req=>{
        const u=new URL(req.url());
        if (['PUT','PATCH','DELETE'].includes(req.method()) ||
            req.method()==='POST' && (u.pathname.startsWith('/api/resource/') || u.pathname.startsWith('/api/method/centrochange_core.'))) writes.push(u.pathname);
      });
      try {
        await page.goto(base+'/login');
        await page.locator('#login_email').fill(fixture.users.f.name);
        await page.locator('#login_password').fill(fixture.users.f.password);
        await page.getByRole('button',{name:'Continua'}).click();
        await page.waitForURL(url=>/^\/(app|desk)/.test(new URL(url).pathname));
        await page.goto(base+'/app/cc-unified-desk?cc_view=finance&cc_fin_view=Banca');
        await page.locator('#finance-content tbody tr').first().waitFor();
        const names=await page.locator('#finance-content tbody tr').evaluateAll(rows=>rows.map(r=>r.dataset.name).filter(Boolean));
        let selected;
        for(const name of names){
          const value=await page.evaluate(async name=>(await(await fetch('/api/method/centrochange_core.finance.banking.candidates?'+new URLSearchParams({name}))).json()).message,name);
          if(value.reconciled_documents?.length){selected={name,value};break;}
        }
        assert(selected,'A reconciled demo movement must exist');
        await page.locator(`#finance-content tr[data-name="${selected.name}"]`).click();
        await page.locator('#detail h3').waitFor();
        const detail=await page.locator('#detail').innerText();
        for(const row of selected.value.reconciled_documents) {
          assert(detail.includes(row.name),'Actual invoice absent from bank detail');
          assert(detail.includes(Number(row.allocated_amount).toLocaleString('it-IT',{minimumFractionDigits:2})),'Allocation amount absent');
        }
        assert.equal(await page.locator('#bank-reconcile').count(),0);
        await page.screenshot({path:path.join(output,`bank-trace-${width}.png`),fullPage:true});
        await page.locator('#bank-cancel').click();
        await page.locator('#modal [name=reason]').waitFor();
        assert(await page.locator('#modal [name=confirm]').isVisible(),'Missing explicit cancel confirmation');
        await page.locator('#modal-dismiss').click();
        await page.goto(base+'/app/cc-unified-desk?cc_view=finance');
        await page.locator('#compare-from-summary').waitFor();
        await page.locator('#compare-from-summary').click();
        await page.locator('#modal [name=expectations]').waitFor();
        const options=await page.locator('#modal [name=expectations] option').evaluateAll(rows=>rows.map(r=>({id:r.value,label:r.textContent})));
        assert(options.length>0);
        assert(options.every(r=>r.label!==r.id && /\d{2}\/\d{2}\/\d{4}/.test(r.label)));
        const ids=await page.evaluate(async center=>(await(await fetch('/api/method/centrochange_core.finance.reporting.records?'+new URLSearchParams({center,doctype:'CC Professional Expectation'}))).json()).message.map(r=>r.name),fixture.centers[0]);
        assert.deepEqual(options.map(r=>r.id).sort(),ids.sort());
        await page.screenshot({path:path.join(output,`comparison-${width}.png`),fullPage:true});
        assert.deepEqual(errors,[]);assert.deepEqual(writes,[]);
        results.push({width,status:'PASS',checks:['actual bank document and amount','reconciled state excludes repeat match','cancel requires explicit confirmation and reason','comparison readable date and canonical IDs'],business_mutations:0});
      } catch(e) {
        await page.screenshot({path:path.join(output,`failure-${width}.png`),fullPage:true});
        results.push({width,status:'FAIL',error:e.message,errors,writes});
      } finally {await context.close();}
    }
  } finally {await browser.close();}
  fs.writeFileSync(path.join(output,'result.json'),JSON.stringify(results,null,2));
  console.log(JSON.stringify(results));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
