// Read-only synthetic record fingerprint before/after the #79 CSS switch.
const {chromium}=require('playwright');
const {createHash}=require('node:crypto');
const fs=require('node:fs');
const fixtureFile=process.env.CC_ISSUE79_FIXTURE;
if(!fixtureFile)throw Error('CC_ISSUE79_FIXTURE is required');
const privateFixture=JSON.parse(fs.readFileSync(fixtureFile,'utf8'));
const users=(privateFixture.fixture||privateFixture).users;
const base=process.env.CC_BASE_URL||'http://centrochange.local:8082';
const digest=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');

(async()=>{
 const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server']});
 const fingerprints=[];
 try{
  for(const role of ['m','s','a','b','c']){
   const context=await browser.newContext({serviceWorkers:'block',locale:'it-IT'}),page=await context.newPage();
   try{
    await page.goto(base+'/login?redirect-to=/app/cc-unified-desk%3Fcc_view%3Dagenda');
    await page.locator('#login_email').fill(users[role].name);
    await page.locator('#login_password').fill(users[role].password);
    await page.getByRole('button',{name:'Continua'}).click();
    await page.locator('#new-booking').waitFor();
    const observed=await page.evaluate(async()=>{
     const centers=[...document.querySelector('#center').options].filter(x=>x.value).map(x=>x.value).sort();
     const read=async(name,center)=>{
      const url='/api/method/centrochange_core.operations.workspace.'+name+'?'+new URLSearchParams({center,query:''});
      const response=await fetch(url,{credentials:'same-origin'});
      if(!response.ok)throw Error(name+' HTTP '+response.status);
      return (await response.json()).message;
     };
     const rows=[];
     for(const center of centers){
      const boot=await read('bootstrap',center),found=await read('patient_search',center);
      rows.push({center,patients:found.patients.map(x=>x.name).sort(),professionals:(boot.practitioners||[]).map(x=>x.name).sort()});
     }
     return rows;
    });
    fingerprints.push({role,centers:observed.length,patients:observed.reduce((n,x)=>n+x.patients.length,0),professionals:observed.reduce((n,x)=>n+x.professionals.length,0),sha256:digest(observed)});
   }finally{await context.close();}
  }
  console.log(JSON.stringify({status:'PASS',route:'/app/cc-unified-desk?cc_view=agenda',roles:fingerprints,sha256:digest(fingerprints),mutations:'NONE'}));
 }finally{await browser.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1});
