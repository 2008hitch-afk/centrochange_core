// Native List -> Form rendering probe; deliberately never edits or saves.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const fixture=JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8'));
const user=(fixture.fixture||fixture).users.m;
const out=process.env.CC_ISSUE137_OUTPUT;
const base=process.env.CC_BASE_URL||'http://centrochange.local:8082';
if(!out||!user)throw Error('Private fixture/output missing');
const routes=['patient','healthcare-practitioner','sales-invoice','purchase-invoice','payment-entry',
  'bank-transaction','item','item-price','appointment-type','cc-center-service','cc-package-template'];

(async()=>{
 const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
 const context=await browser.newContext({viewport:{width:1440,height:900},locale:'it-IT',timezoneId:'Europe/Rome',serviceWorkers:'block'});
 const page=await context.newPage(),results=[];
 try{
  await page.goto(base+'/login');await page.locator('#login_email').fill(user.name);
  await page.locator('#login_password').fill(user.password);
  await page.getByRole('button',{name:'Continua'}).click();await page.locator('#cc-desk-sidebar').waitFor();
  for(const route of routes){
   const errors=[];const onError=e=>errors.push(String(e.message).slice(0,250));page.on('pageerror',onError);
   await page.goto(base+'/app/'+route,{waitUntil:'domcontentloaded'});await page.waitForTimeout(1000);
   const first=page.locator('.list-row .list-subject a, .list-row .level-left a[href]').first();
   let status='BLOCKED_NO_RECORD',reason='',form=null;
   try{
    if(await first.count()){
     await first.click({timeout:6000});await page.waitForTimeout(800);
     form=await page.evaluate(()=>{
      const el=document.querySelector('.form-page'),icons=[...document.querySelectorAll('svg,.icon')].filter(x=>{const r=x.getBoundingClientRect();return r.width>1&&r.height>1});
      return {urlPath:location.pathname,hasForm:!!el&&el.getBoundingClientRect().height>0,
        maxIconPx:Math.round(Math.max(0,...icons.map(x=>Math.max(x.getBoundingClientRect().width,x.getBoundingClientRect().height)))),
        overflowPx:Math.max(0,document.documentElement.scrollWidth-innerWidth)};
     });
     status=form.hasForm&&form.maxIconPx<=96&&form.overflowPx<=3?'PASS':'FAIL';
     reason=!form.hasForm?'FORM_MISSING':form.maxIconPx>96?'OVERSIZED_ICONS':form.overflowPx>3?'HORIZONTAL_OVERFLOW':'';
     await page.screenshot({path:path.join(out,`detail-${route}.png`),fullPage:true,animations:'disabled'});
    }
   }catch(e){status='BLOCKED_INTERACTION';reason=String(e.message).slice(0,200);}
   page.off('pageerror',onError);
   results.push({route,status,reason,form,pageErrors:errors});
   console.error(`${route}: ${status} ${reason}`);
  }
  fs.writeFileSync(path.join(out,'issue137-native-details.json'),JSON.stringify({results},null,2));
  console.log(JSON.stringify({status:'RECORDED',pass:results.filter(x=>x.status==='PASS').length,fail:results.filter(x=>x.status==='FAIL').length,blocked:results.filter(x=>x.status.startsWith('BLOCKED')).length}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
