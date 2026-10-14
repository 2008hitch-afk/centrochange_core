// Click through the live client sidebar in one authenticated session.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.CC_BASE_URL||'http://centrochange.local:8082';
const users=(JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8')).fixture||JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8'))).users;
const out=process.env.CC_ISSUE137_OUTPUT;
if(!out||!users?.m)throw Error('Private fixture/output required');
const steps=[['Agenda','Agenda'],['Ricerca pazienti','Ricerca pazienti'],['Report professionisti','Report professionisti'],
 ['Fatture pazienti','Fatture pazienti'],['Finanza','Finanza'],['Agenda ritorno','Agenda']];
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server']});
 const context=await browser.newContext({viewport:{width:1440,height:900},locale:'it-IT',serviceWorkers:'block'});
 const page=await context.newPage(),rows=[];let fullLoads=0;
 page.on('load',()=>fullLoads++);
 try{
  await page.goto(base+'/login');await page.locator('#login_email').fill(users.m.name);
  await page.locator('#login_password').fill(users.m.password);
  await page.getByRole('button',{name:'Continua'}).click();await page.locator('#cc-desk-sidebar').waitFor();
  const initialLoads=fullLoads;
  for(let i=0;i<steps.length;i++){
   const [label,target]=steps[i];
   if(target==='Fatture pazienti'||target==='Finanza'){
    const section=page.locator('#cc-desk-sidebar details').filter({has:page.locator('summary',{hasText:'Amministrazione'})});
    if(!await section.evaluate(el=>el.open))await section.locator('summary').click();
   }
   const link=page.locator('#cc-desk-sidebar a').filter({has:page.locator('.nav-link-title',{hasText:target})}).first();
   const before=page.url();await link.click();await page.waitForTimeout(1000);
   const after=page.url();
   const shell=await page.evaluate(()=>({sidebar:!!document.querySelector('#cc-desk-sidebar'),
     navbar:!!document.querySelector('#cc-desk-global-nav'),
     giantIcons:[...document.querySelectorAll('svg,.icon')].filter(x=>Math.max(x.getBoundingClientRect().width,x.getBoundingClientRect().height)>96).length}));
   rows.push({label,beforePath:new URL(before).pathname,afterPath:new URL(after).pathname+new URL(after).search,
     routeChanged:before!==after,loadsSinceLogin:fullLoads-initialLoads,...shell});
   await page.screenshot({path:path.join(out,`nav-${i}-${label.replace(/\s+/g,'-').toLowerCase()}.png`),fullPage:true});
  }
  fs.writeFileSync(path.join(out,'issue137-navigation.json'),JSON.stringify({rows},null,2));
  console.log(JSON.stringify({rows}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
