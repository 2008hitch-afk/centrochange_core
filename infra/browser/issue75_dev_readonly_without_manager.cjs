// Issue #75: defer only Manager login after authorised password reset; retain all other read-only API gates.
const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
const f=JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8'));
const out=process.env.CC_ISSUE137_OUTPUT,base=process.env.CC_BASE_URL;
const report={critical:[],functional:[],deferred_roles:['m'],mutative:{status:'BLOCKED',reason:'Accounting fixture cleanup concurrency/retention not yet verified'}};
const check=(list,name,ok,detail={})=>list.push({name,status:ok?'PASS':'FAIL',...detail});
(async()=>{const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
try{
 for(const role of ['guest','s','a','b','c','f','t']){
  const ctx=await browser.newContext({viewport:{width:['s','c','t'].includes(role)?390:1440,height:900},locale:'it-IT'}),p=await ctx.newPage();
  try{
   if(role!=='guest'){
    await p.goto(base+'/login');await p.locator('#login_email').fill(f.users[role].name);await p.locator('#login_password').fill(f.users[role].password);await p.getByRole('button',{name:'Continua',exact:true}).click();await p.waitForURL(u=>/^\/(app|desk)/.test(new URL(u).pathname));
    check(report.critical,role+':login',true);
    try{await p.locator('#cc-desk-sidebar').waitFor({timeout:15000});await p.screenshot({path:path.join(out,role+'.png'),fullPage:true});check(report.functional,role+':shell',true);}catch(e){check(report.functional,role+':shell',false,{error:e.name});}
   }else await p.goto(base+'/login');
   const get=async url=>p.evaluate(async url=>{const r=await fetch(url);const text=await r.text();let data;try{data=JSON.parse(text)}catch{}return {status:r.status,data,text};},url);
   const args=new URLSearchParams({center:f.centers[0],start:'2026-01-01',end:'2026-12-31',report:'general_ledger'});
   const prefix='/api/method/centrochange_core.finance.native_reports.';
   for(const name of ['general_ledger','trial_balance']){
    args.set('report',name);const r=await get(prefix+'run?'+args);
    if(['guest','a','b','c'].includes(role))check(report.critical,role+':'+name+':denied',[401,403].includes(r.status),{http:r.status});
    else check(report.functional,role+':'+name,r.status===200&&r.data?.message?.read_only===true&&r.data.message.columns.length>0,{http:r.status,rows:r.data?.message?.rows?.length,exception:r.data?.exc_type});
   }
   args.set('center',f.centers[1]);const cross=await get(prefix+'run?'+args);
   check(report.critical,role+':inactive-center-denied',[401,403].includes(cross.status),{http:cross.status});
   if(!['guest','a','b','c'].includes(role)){
    args.set('center',f.centers[0]);args.set('report','general_ledger');const csv=await get(prefix+'export_csv?'+args);check(report.functional,role+':csv',csv.status===200&&csv.text.length>10&&!csv.data?.exc_type,{http:csv.status,bytes:csv.text.length});
   }
   if(!['a'].includes(role)){
    const note=await get('/api/resource/CC%20Private%20Note/'+encodeURIComponent(f.private_note));
    check(report.critical,role+':private-note-denied',[401,403].includes(note.status),{http:note.status});
   }
  }catch(e){check(report.critical,role+':execution',false,{error:e.name});}
  finally{await ctx.close();}
 }
}finally{await browser.close();}
report.status=report.critical.every(x=>x.status==='PASS')?'ESSENTIAL_PASS':'CRITICAL_FAIL';
fs.writeFileSync(path.join(out,'devfirst-readonly.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({status:report.status,critical:report.critical.length,functional:report.functional.length}));
process.exitCode=report.status==='ESSENTIAL_PASS'?0:2;
})().catch(e=>{console.error(e.name);process.exitCode=2});
