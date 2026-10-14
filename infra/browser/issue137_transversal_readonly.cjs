// Read-only cross-role/localization/center observations; does not assert new features already exist.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.CC_BASE_URL||'http://centrochange.local:8082';
const users=(JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8')).fixture||JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8'))).users;
const out=process.env.CC_ISSUE137_OUTPUT;
if(!users||!out)throw Error('Private fixture/output required');
const views=[
 ['agenda','/app/cc-unified-desk?cc_view=agenda'],
 ['ricerca','/app/cc-unified-desk?cc_view=agenda&cc_ops_view=Pazienti'],
 ['finanza','/app/cc-unified-desk?cc_view=finance'],
 ['ts','/app/cc-unified-desk?cc_view=finance&cc_fin_view=TS'],
 ['report','/app/cc-unified-desk?cc_view=professional'],
 ['audit','/app/cc-unified-desk?cc_view=audit'],
 ['fattura','/app/sales-invoice']
];
const method=async(page,doctype)=>{
 const query=new URLSearchParams({doctype,fields:JSON.stringify(['name']),limit_page_length:'100'});
 return page.evaluate(async url=>{const r=await fetch(url,{credentials:'same-origin'});let j;try{j=await r.json();}catch{}return {status:r.status,count:Array.isArray(j?.message)?j.message.length:null,errorType:j?.exc_type||null};},'/api/method/frappe.client.get_list?'+query);
};
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
 const result={roles:{},guest:{}};
 try{
  for(const role of ['m','s','a','b','c','f','t']){
   const context=await browser.newContext({viewport:{width:1440,height:900},locale:'it-IT',timezoneId:'Europe/Rome',serviceWorkers:'block'});
   const page=await context.newPage();
   await page.goto(base+'/login');await page.locator('#login_email').fill(users[role].name);
   await page.locator('#login_password').fill(users[role].password);
   await page.getByRole('button',{name:'Continua'}).click();await page.locator('#cc-desk-sidebar').waitFor();
   const entry={api:{patient:await method(page,'Patient'),invoice:await method(page,'Sales Invoice')},views:[]};
   if(role==='m'){
    for(const [name,url] of views){
     await page.goto(base+url,{waitUntil:'domcontentloaded'});await page.waitForTimeout(950);
     const defaultCenter=await page.locator('#center').count()?await page.locator('#center option:checked').allTextContents():[];
     if(await page.locator('#center option',{hasText:'Centro A'}).count()){
      await page.locator('#center').selectOption({label:'Centro A'});await page.waitForTimeout(550);
     }else if(await page.locator('#center option',{hasText:/^A$/}).count()){
      await page.locator('#center').selectOption({label:'A'});await page.waitForTimeout(550);
     }
     const observation=await page.evaluate(()=>{
      const text=document.body.innerText||'';
      const count=regex=>(text.match(regex)||[]).length;
      const center=document.querySelector('#center');
      return {isoDateCount:count(/\b20\d{2}-\d{2}-\d{2}\b/g),ampmCount:count(/\b\d{1,2}:\d{2}\s*(?:AM|PM)\b/gi),
        englishTerms:Object.fromEntries(['Session','Get Items From','Sales Taxes and Charges','Stock','Protected note revision'].map(x=>[x,text.includes(x)])),
        centerOptions:center?[...center.options].map(x=>x.textContent.trim()).filter(Boolean):[],
        bodyChars:text.length};
     });
     entry.views.push({name,defaultCenter,...observation});
    }
    await page.goto(base+views[0][1]);
    await page.waitForFunction(()=>document.querySelector('#center')?.options.length>0);
    const center=page.locator('#center');
    if(await center.locator('option',{hasText:'Centro A'}).count())await center.selectOption({label:'Centro A'});
    await page.locator('#new-booking').waitFor({state:'visible',timeout:10000});
    await page.locator('#new-booking').click();
    entry.bookingModal=await page.evaluate(()=>{
     const modal=document.querySelector('#modal');const text=modal?.innerText||'';
     return {ampmCount:(text.match(/\b\d{1,2}:\d{2}\s*(?:AM|PM)\b/gi)||[]).length,
       timeInputs:[...(modal?.querySelectorAll('input')||[])].filter(x=>/time|ora/i.test((x.name||'')+' '+(x.placeholder||'')+' '+(x.type||''))).map(x=>({type:x.type,placeholder:x.placeholder||'',ariaLabel:x.getAttribute('aria-label')||''}))};
    });
    await page.screenshot({path:path.join(out,'issue137-booking-modal-localization.png'),fullPage:true});
    await page.goto(base+views[0][1]);
    await page.waitForFunction(()=>document.querySelector('#center')?.options.length>0);
    await page.locator('#center').selectOption({label:'Centro A'});
    await page.locator('.calendar-appointment').first().click();
    await page.waitForTimeout(650);
    entry.appointmentDetail=await page.evaluate(()=>{
     const text=document.body.innerText||'';
     return {isoDateCount:(text.match(/\b20\d{2}-\d{2}-\d{2}\b/g)||[]).length,
       rawSessionTerm:/\bSession\b/.test(text),
       actionLabels:['Riapri','Chiudi','Sposta','Cancella','Rinuncia economica','Pagata'].filter(x=>text.includes(x))};
    });
    await page.screenshot({path:path.join(out,'issue137-appointment-detail.png'),fullPage:true});
    await page.getByRole('tab',{name:'Storico'}).click();await page.waitForTimeout(550);
    entry.appointmentHistory=await page.locator('#detail').evaluate(el=>({
      isoDateCount:(el.innerText.match(/\b20\d{2}-\d{2}-\d{2}\b/g)||[]).length,
      hasBeforeAfter:/\bprima\b.*\bdopo\b/i.test(el.innerText),bodyChars:el.innerText.length
    }));
    await page.screenshot({path:path.join(out,'issue137-appointment-history.png'),fullPage:true});
    await page.getByRole('tab',{name:'Note'}).click();await page.waitForTimeout(550);
    entry.appointmentNotes=await page.locator('#detail').evaluate(el=>({
      hasRevisionLabel:/rettifica|revisione|versione/i.test(el.innerText),bodyChars:el.innerText.length
    }));
    await page.screenshot({path:path.join(out,'issue137-appointment-notes.png'),fullPage:true});
   }
   result.roles[role]=entry;await context.close();
  }
  const guest=await browser.newContext({serviceWorkers:'block'}),page=await guest.newPage();
  await page.goto(base+'/login');
  result.guest.patient=await method(page,'Patient');result.guest.invoice=await method(page,'Sales Invoice');
  await guest.close();
  fs.writeFileSync(path.join(out,'issue137-transversal.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
