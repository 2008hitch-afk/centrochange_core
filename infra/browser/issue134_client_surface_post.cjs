/* Read-only localization sweep of routes exposed by each demo role. */
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');

const base = process.env.CC_BASE_URL || 'http://centrochange.local:8082';
const fixture = JSON.parse(fs.readFileSync(process.env.CC_DEMO_FIXTURE, 'utf8'));
const users = (fixture.fixture || fixture).users;
const output = process.env.CC_LOCALE_OUTPUT;
if (!output || !users) throw Error('Private fixture/output required');
fs.mkdirSync(output, {recursive:true, mode:0o700});
const english = /\b(?:Occupation|Marital Status|Appointments and Encounters|Billing and Payments|Annual Billing|Total Unpaid|Free Followup Details|Address and Contacts|Immutable Incoming Source|Get Items From|No results|Required|Mandatory|Save|Submit|Cancel)\b/i;

async function main() {
  const browser = await chromium.launch({headless:true,args:[
    '--host-resolver-rules=MAP centrochange.local 127.0.0.1',
    '--no-proxy-server','--disable-dev-shm-usage']});
  const rows=[];
  try {
    for (const role of ['m','s','a','b','c','f','t']) for (const width of [1440,390]) {
      const context=await browser.newContext({viewport:{width,height:900},locale:'it-IT',
        timezoneId:'Europe/Rome',serviceWorkers:'block'});
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      try {
        await page.goto(base+'/login',{waitUntil:'domcontentloaded'});
        await page.locator('#login_email').fill(users[role].name);
        await page.locator('#login_password').fill(users[role].password);
        await page.getByRole('button',{name:'Continua'}).click();
        await page.locator('#cc-desk-sidebar').waitFor({timeout:30000});
        const links=await page.locator('#cc-desk-sidebar a[href]').evaluateAll(anchors=>
          [...new Set(anchors.map(a=>a.getAttribute('href')).filter(h=>h?.startsWith('/app/')))]);
        for (const href of links) {
          try {
            await page.goto(base+href,{waitUntil:'domcontentloaded',timeout:30000});
            await page.locator('#cc-desk-sidebar').waitFor({timeout:30000});
            await page.waitForTimeout(350);
            const data=await page.evaluate(pattern=>{
              const rex=new RegExp(pattern,'i');
              const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
              const labels=[...document.querySelectorAll('h1,h2,h3,label,button,.page-title,.control-label,.section-head,[placeholder]')]
                .filter(visible).map(el=>(el.getAttribute('placeholder')||el.textContent||'').trim()).filter(Boolean);
              return {title:document.title,matched:[...new Set(labels.filter(x=>rex.test(x)))],
                hasMain:!!document.querySelector('.page-wrapper,.layout-main-section,.cc-unified-desk'),
                overflow:document.documentElement.scrollWidth-innerWidth,
                active:document.querySelectorAll('#cc-desk-sidebar a.active').length};
            },english.source);
            rows.push({role,width,href,status:data.hasMain?'PASS':'FAIL',...data});
          } catch(e){rows.push({role,width,href,status:'FAIL',reason:String(e.message).slice(0,180)});}
        }
        await page.screenshot({path:path.join(output,`role-${role}-${width}.png`),animations:'disabled'});
      } catch(e){rows.push({role,width,href:'login',status:'FAIL',reason:String(e.message).slice(0,180)});}
      rows.push({role,width,href:'javascript',status:errors.length?'FAIL':'PASS',errors:errors.slice(0,5)});
      await context.close();
    }
  } finally {await browser.close();}
  fs.writeFileSync(path.join(output,'client-surfaces.json'),JSON.stringify(rows,null,2));
  const visited=rows.filter(x=>x.href?.startsWith('/app/'));
  const summary={routes:visited.length,failed:rows.filter(x=>x.status==='FAIL').length,
    english:visited.filter(x=>x.matched?.length).map(({role,width,href,matched})=>({role,width,href,matched}))};
  console.log(JSON.stringify(summary));
  if(summary.failed)process.exitCode=1;
}
main().catch(e=>{console.error(String(e.stack));process.exitCode=1});
