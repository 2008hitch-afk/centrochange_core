// Read-only checks for the two export paths not fully characterized by the sweep.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const fixture=JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8'));
const results=[];
(async()=>{
  const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
  try{
    for(const role of ['m','f','t','a']){
      const context=await browser.newContext({locale:'it-IT'}),page=await context.newPage();
      try{
        await page.goto(process.env.CC_BASE_URL+'/login');
        await page.locator('#login_email').fill(fixture.users[role].name);
        await page.locator('#login_password').fill(fixture.users[role].password);
        await page.getByRole('button',{name:'Continua',exact:true}).click();
        await page.waitForURL(u=>new URL(u).pathname!='/login');
        for(const [kind,method,extra] of [
          ['professional','centrochange_core.finance.reporting.professional_export',{practitioner:fixture.practitioners[0]}],
          ['trial_balance','centrochange_core.finance.native_reports.export_csv',{report:'trial_balance'}],
        ]){
          const query=new URLSearchParams({center:fixture.centers[0],start:'2026-01-01',end:'2026-12-31',...extra});
          const result=await page.evaluate(async url=>{const response=await fetch(url);const body=await response.text();return {status:response.status,type:response.headers.get('content-type')||'',header:body.split(/\r?\n/)[0],europeanDate:/\b\d{2}\/\d{2}\/\d{4}\b/.test(body),isoDate:/\b20\d{2}-\d{2}-\d{2}\b/.test(body),rows:body.split(/\r?\n/).length-1};},'/api/method/'+method+'?'+query);
          results.push({role,kind,status:result.status,csv:result.type.startsWith('text/csv'),italianHeader:/Identificativo seduta|Data|Ora|Conto|Debito|Credito|Saldo/.test(result.header),europeanDate:result.europeanDate,isoDate:result.isoDate,rows:result.rows});
        }
      }finally{await context.close();}
    }
  }finally{await browser.close();}
  fs.writeFileSync(path.join(process.env.CC_ISSUE137_OUTPUT,'export-remaining.json'),JSON.stringify({results},null,2));
  console.log(JSON.stringify({results}));
})().catch(error=>{console.error(error.name);process.exit(2)});
