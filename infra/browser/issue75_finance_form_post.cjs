/* Read-only finance Form check, waits for asynchronous native Form refresh. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const base=process.env.CC_BASE_URL||'http://centrochange.local:8082';
const fixture=JSON.parse(fs.readFileSync(process.env.CC_DEMO_FIXTURE,'utf8'));
const users=(fixture.fixture||fixture).users;
const output=process.env.CC_UX_OUTPUT;
assert(output&&users.m&&users.f,'private fixture and output required');
fs.mkdirSync(output,{recursive:true,mode:0o700});

(async()=>{
 const browser=await chromium.launch({headless:true,args:[
   '--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
 const rows=[];
 try {
  for(const [role,route] of [['m','sales-invoice'],['f','purchase-invoice']])
   for(const width of [1440,390]) {
    const context=await browser.newContext({viewport:{width,height:900},locale:'it-IT',serviceWorkers:'block'});
    const page=await context.newPage(),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    try {
     await page.goto(base+'/login');
     await page.locator('#login_email').fill(users[role].name);
     await page.locator('#login_password').fill(users[role].password);
     await page.getByRole('button',{name:'Continua'}).click();
     await page.locator('#cc-desk-sidebar').waitFor();
     await page.goto(base+'/app/'+route);
     await page.locator('.list-row .list-subject a').first().click();
     await page.locator('.cc-finance-context').waitFor({state:'visible',timeout:20000});
     const result=await page.evaluate(()=>({
      guide:document.querySelector('.cc-finance-context').innerText.includes('Come compilare'),
      native:!!document.querySelector('.form-layout'),
      overflow:document.documentElement.scrollWidth-innerWidth,
      docstatus:window.cur_frm?.doc?.docstatus,
      active:document.querySelectorAll('#cc-desk-sidebar a.active').length}));
     assert(result.guide&&result.native&&result.overflow<=2&&result.active===1,
       `${route}/${width}: native context, layout or navigation failed`);
     assert.equal(errors.length,0,`${route}/${width}: page errors`);
     await page.screenshot({path:path.join(output,`${route}-${role}-${width}-post.png`),
       fullPage:true,animations:'disabled'});
     rows.push({role,route,width,status:'PASS',...result});
    } catch(e) {rows.push({role,route,width,status:'FAIL',reason:String(e.message).slice(0,260)});}
    finally {await context.close();}
   }
 } finally {await browser.close();}
 fs.writeFileSync(path.join(output,'issue75-finance-post.json'),JSON.stringify(rows,null,2));
 console.log(JSON.stringify({status:rows.every(x=>x.status==='PASS')?'PASS':'FAIL',passed:rows.filter(x=>x.status==='PASS').length,total:rows.length}));
 if(rows.some(x=>x.status!=='PASS')) process.exitCode=1;
})().catch(e=>{console.error(e.stack);process.exitCode=1});
