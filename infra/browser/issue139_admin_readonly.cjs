// Technical Administrator stays on native Desk; read-only W5 boundary check.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const credentials=JSON.parse(fs.readFileSync(process.env.CC_ISSUE139_ADMIN_FIXTURE,'utf8'));
const output=process.env.CC_ISSUE137_OUTPUT;
if(!output||credentials.name!=='Administrator'||!credentials.password)throw Error('private Administrator fixture required');
const base=process.env.CC_BASE_URL||'http://centrochange.local:8082';
(async()=>{
 const browser=await chromium.launch({headless:true,args:[
  '--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
 const context=await browser.newContext({viewport:{width:1440,height:900},locale:'it-IT',serviceWorkers:'block'});
 const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.goto(base+'/login',{waitUntil:'domcontentloaded'});
  await page.locator('#login_email').fill(credentials.name);
  await page.locator('#login_password').fill(credentials.password);
  await page.getByRole('button',{name:'Continua'}).click();
  await page.waitForURL(u=>new URL(u).pathname.startsWith('/app'),{timeout:30000});
  const response=await page.goto(base+'/app',{waitUntil:'domcontentloaded'});
  const user=await page.evaluate(async()=>{
   const r=await fetch('/api/method/frappe.auth.get_logged_user',{credentials:'same-origin'});
   return r.ok?(await r.json()).message:null;
  });
  assert.equal(response.status(),200);
  assert.equal(user,'Administrator');
  assert.equal(errors.length,0);
  assert(await page.locator('body').innerText().then(t=>t.length>100));
  const screenshot=path.join(output,'issue139-administrator.png');
  await page.screenshot({path:screenshot,fullPage:true});
  const guest=await browser.newContext({serviceWorkers:'block'});
  const guestPage=await guest.newPage();
  await guestPage.goto(base+'/login',{waitUntil:'domcontentloaded'});
  const guestStatus=await guestPage.evaluate(async()=>{
   const query=new URLSearchParams({doctype:'Patient',fields:JSON.stringify(['name']),limit_page_length:'1'});
   return (await fetch('/api/method/frappe.client.get_list?'+query,{credentials:'same-origin'})).status;
  });
  await guest.close();
  assert([401,403].includes(guestStatus),'Guest Patient API must deny');
  console.log(JSON.stringify({status:'PASS',role:user,guest_patient_api:guestStatus,errors:0,
   screenshot:path.basename(screenshot)}));
 }finally{await context.close();await browser.close()}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
