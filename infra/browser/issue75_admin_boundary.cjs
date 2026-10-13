// Technical Administrator retains the upstream Desk; no CC client shell.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const secret=fs.readFileSync('/qa-runtime.env','utf8').split('\n').find(x=>x.startsWith('ADMIN_PASSWORD='));
assert(secret,'private Administrator credential unavailable');
const password=secret.slice('ADMIN_PASSWORD='.length).replace(/^['"]|['"]$/g,'');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:900},locale:'it-IT'});
  await page.goto('http://centrochange.local:8080/login');
  await page.locator('#login_email').fill('Administrator');
  await page.locator('#login_password').fill(password);
  await page.locator('.form-login button[type="submit"]').click();
  await page.waitForURL(url=>!url.pathname.startsWith('/login'),{timeout:30000});
  await page.goto('http://centrochange.local:8080/app/patient');
  await page.locator('.page-head').waitFor({timeout:30000});
  await page.locator('.list-row-head').waitFor({timeout:30000});
  assert.equal(await page.evaluate(()=>frappe.session.user),'Administrator');
  assert.equal(await page.locator('body.cc-client-desk').count(),0);
  assert.equal(await page.locator('#cc-desk-sidebar,#cc-desk-global-nav').count(),0);
  assert.equal(await page.locator('.list-row-head').count(),1);
  console.log(JSON.stringify({status:'PASS',technical_administrator:'native Desk',client_shell:false}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
