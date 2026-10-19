// Inspect served human-facing CSV exports without retaining their data in evidence.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const fixture=JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8'));
const center=fixture.centers[0];
const args=new URLSearchParams({center,start:'2026-01-01',end:'2026-12-31'});
const targets=[
  ['finance','centrochange_core.finance.reporting.export_csv'],
  ['patients','centrochange_core.finance.patient_reporting.patient_export'],
  ['agenda','centrochange_core.operations.reporting.export_csv',new URLSearchParams({center,start:'2026-09-01',end:'2026-11-30'})],
  ['general_ledger','centrochange_core.finance.native_reports.export_csv',new URLSearchParams({...Object.fromEntries(args),report:'general_ledger'})],
  ['trial_balance','centrochange_core.finance.native_reports.export_csv',new URLSearchParams({...Object.fromEntries(args),report:'trial_balance'})],
];
const checks=[];
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
        for(const [name,method,query] of targets){
          const result=await page.evaluate(async url=>{
            const response=await fetch(url),body=await response.text();
            return {status:response.status,type:response.headers.get('content-type')||'',
              header:body.split(/\r?\n/)[0],europeanDate:/\b\d{2}\/\d{2}\/\d{4}\b/.test(body),
              isoDate:/\b20\d{2}-\d{2}-\d{2}\b/.test(body),bytes:body.length};
          },'/api/method/'+method+'?'+(query||args));
          checks.push({role,name,status:result.status,csv:result.type.startsWith('text/csv'),
            italianHeader:/Tipo|Data|Riferimento|Documento|Professionista/.test(result.header),
            europeanDate:result.europeanDate,isoDate:result.isoDate,bytes:result.bytes});
        }
      }finally{await context.close();}
    }
  }finally{await browser.close();}
  fs.writeFileSync(path.join(process.env.CC_ISSUE137_OUTPUT,'exports-readonly.json'),JSON.stringify({checks},null,2));
  console.log(JSON.stringify({checks}));
})().catch(e=>{console.error(e.stack);process.exit(2)});
