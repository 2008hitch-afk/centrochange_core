// Narrow, read-only follow-up for the two functional surfaces not resolved by install gate.
const {chromium}=require('playwright'),fs=require('node:fs'),path=require('node:path');
const base=process.env.CC_BASE_URL,fixture=JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8'));
const output=process.env.CC_ISSUE137_OUTPUT;const checks=[];
(async()=>{const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
try{for(const role of ['f','t','a']){const ctx=await browser.newContext({locale:'it-IT'}),p=await ctx.newPage();
try{await p.goto(base+'/login');await p.locator('#login_email').fill(fixture.users[role].name);await p.locator('#login_password').fill(fixture.users[role].password);await p.getByRole('button',{name:'Continua',exact:true}).click();await p.waitForURL(u=>/^\/(app|desk)/.test(new URL(u).pathname));
const query=new URLSearchParams({center:fixture.centers[0],report:'general_ledger',start:'2026-01-01',end:'2026-12-31'});
const report=await p.evaluate(async q=>{const r=await fetch('/api/method/centrochange_core.finance.native_reports.export_csv?'+q);const body=await r.text();return {status:r.status,type:r.headers.get('content-type'),header:body.split(/\r?\n/)[0],europeanDate:/\b\d{2}\/\d{2}\/\d{4}\b/.test(body),bytes:body.length};},query.toString());
checks.push({role,kind:'general_ledger_export',status:report.status,contentType:report.type,hasItalianHeader:report.header.includes('Data')||report.header.includes('Tipo'),hasEuropeanDate:report.europeanDate,bytes:report.bytes});
}catch(e){checks.push({role,kind:'runner',status:'BLOCKED',error:e.name});}finally{await ctx.close();}}
}finally{await browser.close();}
fs.writeFileSync(path.join(output,'remaining-readonly.json'),JSON.stringify({checks},null,2));console.log(JSON.stringify({checks}));})().catch(e=>{console.error(e.stack);process.exit(2)});
