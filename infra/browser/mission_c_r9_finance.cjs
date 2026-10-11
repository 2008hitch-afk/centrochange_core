// Read-only coverage of every Finance view inside the isolated Unified Desk.
const {chromium} = require('playwright');
const fs = require('fs');
const assert = require('assert');
const fixture = JSON.parse(fs.readFileSync('/qa-fixture.json')).fixture;
const views = ['Riepilogo','Fatture pazienti','XML ricevuti','Fatture fornitori',
  'Banca','Professionisti','Coda amministrativa','SdI','TS'];

(async () => {
  const browser = await chromium.launch({headless:true,args:[
    '--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server',
    '--no-first-run','--disable-background-networking','--disable-component-update',
    '--disable-default-apps','--disable-sync','--disable-extensions',
    '--disk-cache-size=0','--media-cache-size=0']});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:900},locale:'it-IT'});
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    const base='http://centrochange.local:8080';
    await page.goto(base+'/login?redirect-to='+encodeURIComponent('/app/cc-unified-desk?cc_view=finance'));
    await page.locator('#login_email').fill(fixture.users.f.name);
    await page.locator('#login_password').fill(fixture.users.f.password);
    await page.locator('.form-login button[type="submit"]').click();
    await page.locator('#finance-content').waitFor({timeout:60000});
    const results=[];
    for (const view of views) {
      await page.locator(`#navigation [data-view="${view}"]`).click();
      await page.waitForFunction(() => {
        const node=document.querySelector('#finance-content');
        return node && node.innerText.trim() && !node.innerText.includes('Caricamento…');
      },null,{timeout:30000});
      const result=await page.evaluate(() => ({
        title:document.querySelector('#page-title')?.textContent?.trim(),
        content:document.querySelector('#finance-content')?.innerText?.slice(0,200),
        rows:document.querySelectorAll('#finance-content tr[data-name]').length,
        overflow:document.documentElement.scrollWidth>innerWidth,
        error:document.querySelector('#notice.error')?.textContent?.trim()||''
      }));
      assert.strictEqual(result.title,view);
      assert(result.content && !result.error,`${view}: empty/error content`);
      assert(!result.overflow,`${view}: document overflow`);
      results.push({view,rows:result.rows,contentLength:result.content.length});
    }
    await page.screenshot({path:'/qa-results/r9-finance-desktop.png',fullPage:false});
    await page.setViewportSize({width:390,height:844});
    await page.locator('#navigation [data-view="Riepilogo"]').click();
    await page.waitForFunction(() => document.querySelector('#finance-content')?.innerText.includes('Contabilità del centro'));
    const mobileOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
    await page.screenshot({path:'/qa-results/r9-finance-mobile.png',fullPage:false});
    assert(!mobileOverflow,'Finance mobile document overflow');
    assert.deepStrictEqual(errors,[]);
    console.log(JSON.stringify({status:'PASS',views:results,mobileOverflow,errors:0}));
  } finally {await browser.close();}
})().catch(error=>{console.error(error.stack||error.message);process.exit(1);});
