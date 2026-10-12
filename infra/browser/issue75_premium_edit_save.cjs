// Synthetic service: real native Form save and exact restoration of its source value.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const fixture=JSON.parse(fs.readFileSync('/qa-fixture.json')).fixture;
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage','--disable-gpu']});
 const context=await browser.newContext({viewport:{width:1440,height:900},locale:'it-IT',serviceWorkers:'block'});
 const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://centrochange.local:8080/login?redirect-to=/app/item');
 await page.locator('#login_email').fill(fixture.users.m.name);
 await page.locator('#login_password').fill(fixture.users.m.password);
 await page.locator('.form-login button[type=submit]').click();
 await page.locator('.list-row-head').waitFor({timeout:90000});
 await page.locator('.list-row .list-subject a').first().click();
 await page.locator('.form-layout').waitFor();
 const original=await page.evaluate(()=>cur_frm.doc.description||'');
 const sample='Verifica temporanea interfaccia Centro Change';
 const save=async()=>{await page.getByRole('button',{name:'Salva',exact:true}).click();await page.waitForFunction(()=>!cur_frm.is_dirty(),null,{timeout:30000});};
 let changed=false;
 try{
  await page.locator('.ql-editor[contenteditable=true]').first().fill(sample);
  await page.waitForFunction(()=>cur_frm.is_dirty(),null,{timeout:10000});
  await save();changed=true;
  await page.reload();await page.locator('.form-layout').waitFor();
  assert((await page.evaluate(()=>cur_frm.doc.description||'')).includes(sample),'description did not persist');
 }finally{
  if(changed){
   await page.evaluate(value=>cur_frm.set_value('description',value),original);
   await page.waitForFunction(()=>cur_frm.is_dirty(),null,{timeout:10000});
   await save();
  }
 }
 await page.reload();await page.locator('.form-layout').waitFor();
 assert.equal(await page.evaluate(()=>cur_frm.doc.description||''),original,'original description not restored');
 await page.goto('http://centrochange.local:8080/app/item');
 await page.locator('.list-row-head').waitFor();
 await page.locator('.list-row .list-subject a').first().waitFor({timeout:30000});
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'PASS',doctype:'Item',list_form_edit_save_restore_list:true,original_restored:true,errors}));
 await context.close();await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
