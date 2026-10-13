// Real Chromium presentation checks against local synthetic API stubs. No DEV access.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const http=require('node:http');
const path=require('node:path');
const {chromium}=require('playwright');
const assets=path.resolve(__dirname,'../../app/centrochange_core/centrochange_core/public');
const source=fs.readFileSync(path.join(assets,'js/cc_desk_fragments.js'),'utf8');
const fragments=JSON.parse(source.slice(source.indexOf('{')).trim().replace(/;$/,''));
const json=(response,message)=>{response.setHeader('Content-Type','application/json');response.end(JSON.stringify({message}));};
const reviewed=JSON.stringify({opposition:'No Opposition',eligibility:'SYNTHETIC_ELIGIBLE',expense_amount:10,expense_code:'SYNTHETIC_EXPENSE'});
const server=http.createServer((request,response)=>{
 const url=new URL(request.url,'http://localhost');
 if(url.pathname==='/finance'){
  response.setHeader('Content-Type','text/html; charset=utf-8');
  response.end('<!doctype html><html lang="it"><head><meta name="csrf-token" content="synthetic"><link rel="stylesheet" href="/assets/centrochange_core/css/workspace.css"></head><body class="finance-page"><nav id="navigation"></nav><button id="logout"></button><div class="workspace">'+fragments.finance.page+'</div>'+fragments.finance.modal+'<script type="module" src="/assets/centrochange_core/js/finance_workspace.js"></script></body></html>');return;
 }
 if(url.pathname==='/audit'){
  response.setHeader('Content-Type','text/html; charset=utf-8');
  response.end('<!doctype html><html lang="it"><head><meta name="csrf-token" content="synthetic"><link rel="stylesheet" href="/assets/centrochange_core/css/workspace.css"></head><body><input id="audit-start"><input id="audit-end"><input id="audit-type"><input id="audit-reference"><form id="audit-filters"></form><p id="audit-error"></p><section id="audit-content"></section><button id="audit-prev"></button><button id="audit-next"></button><script type="module" src="/assets/centrochange_core/js/audit_view.js"></script></body></html>');return;
 }
 if(url.pathname==='/notifications'){
  response.setHeader('Content-Type','text/html; charset=utf-8');
  response.end('<!doctype html><html lang="it"><head><meta name="csrf-token" content="synthetic"></head><body><nav id="navigation"></nav><button id="logout"></button>'+fragments.agenda.page+fragments.agenda.modal+'<script>window.ccDeskNavigate=()=>{}</script><script type="module" src="/assets/centrochange_core/js/workspace.js"></script></body></html>');return;
 }
 if(url.pathname.startsWith('/assets/centrochange_core/')){
  const file=path.join(assets,url.pathname.replace('/assets/centrochange_core/',''));
  if(!file.startsWith(assets)||!fs.existsSync(file)){response.statusCode=404;response.end();return;}
  response.setHeader('Content-Type',file.endsWith('.css')?'text/css':'text/javascript');response.end(fs.readFileSync(file));return;
 }
 if(url.pathname.startsWith('/api/resource/File/')){response.setHeader('Content-Type','application/json');response.end(JSON.stringify({data:{file_url:'/private/files/synthetic.xml'}}));return;}
 if(url.pathname.startsWith('/api/resource/CC%20Fiscal%20Transaction/')){response.setHeader('Content-Type','application/json');response.end(JSON.stringify({data:{input_snapshot:reviewed}}));return;}
 if(url.pathname.startsWith('/api/method/')){
  const method=url.pathname.split('/').at(-1);
  if(method.endsWith('reporting.bootstrap'))json(response,{centers:[{name:'A',branch:'Centro A'}],center:'A',can_write:true,is_manager:true,practitioners:[],items:[],accounts:[]});
  else if(method.endsWith('reporting.summary'))json(response,{totals:{revenue_net:0,collected:0,receivable_outstanding:0,purchase_net:0,payable_outstanding:0,expected_compensation:0,sessions:0,unresolved_expectations:0},sales_invoices:[],purchase_invoices:[],exceptions:[]});
  else if(method.endsWith('fiscal.records'))json(response,[{name:'TS-2',reference_name:'SEDUTA-1',status:'READY',attempt_count:0,direction:'OUTBOUND',corrects:'TS-1'},{name:'TS-1',reference_name:'SEDUTA-1',status:'ELIGIBILITY_PENDING',attempt_count:0,direction:'OUTBOUND'}]);
  else if(method.endsWith('fiscal.status'))json(response,{domain:'TS',status:url.searchParams.get('name')==='TS-2'?'READY':'ELIGIBILITY_PENDING',payload_file:'FILE-1',attempts:[]});
  else if(method.endsWith('audit_view.events'))json(response,{events:[{event_type:'SESSION_REOPENED',actor:'cc-http-uat0000001-m@example.invalid',event_time:'2026-10-13 16:56:29',reference_doctype:'Patient Appointment',reference_name:'SESSION-1',reason:'TEST',before_state:'{"state":"Closed"}',after_state:'{"state":"Reopened"}'}],has_more:false});
  else if(method.endsWith('workspace.bootstrap'))json(response,{center:'A',centers:[{name:'A',branch:'Centro A'}],roles:['CC Manager'],practitioners:[],patients:[],services:[]});
  else if(method.endsWith('client.get_list'))json(response,[]);
  else if(method.endsWith('booking_confirmation.records'))json(response,[{name:'CONF-1',recipient:'demo@example.invalid',state:'Simulated Sent',message:'<p>Primo incontro confermato per il 14/10/2026 alle 12:00 con Marco.</p><p>Servizio: Primo incontro · 60 minuti.</p>',last_error:''}]);
  else {response.statusCode=404;json(response,'Unexpected API: '+method);}
  return;
 }
 response.statusCode=404;response.end('Missing');
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,executablePath:process.env.CC_CHROMIUM});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});const errors=[];page.on('pageerror',error=>errors.push(error.message));
  const base=`http://127.0.0.1:${server.address().port}`;
  await page.goto(base+'/finance');await page.locator('#navigation [data-view="TS"]').click();
  await page.locator('#finance-content tr[data-name="TS-2"]').click();
  await page.locator('#ts-reviewed-inputs').waitFor();
  assert.deepEqual(await page.locator('#ts-reviewed-inputs thead th').allTextContents(),['Campo','Valore']);
  assert.match(await page.locator('#ts-reviewed-inputs').innerText(),/Opposizione.*Nessuna opposizione/s);
  assert.match(await page.locator('#detail').innerText(),/Versioni precedenti.*Tentativi simulati.*Payload e azioni/s);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  if(process.env.CC_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.CC_SCREENSHOT_DIR,'ts-mobile-offline.png'),fullPage:true});
  for(const [width,label] of [[768,'tablet'],[1440,'desktop']]){
   await page.setViewportSize({width,height:900});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,label+' overflow');
   if(process.env.CC_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.CC_SCREENSHOT_DIR,'ts-'+label+'-offline.png'),fullPage:true});
  }
  await page.setViewportSize({width:390,height:844});
  await page.locator('#open-previous-fiscal').click();await page.locator('#detail').getByText('Eligibilità da verificare').waitFor();
  await page.goto(base+'/audit');await page.locator('.audit-summary').waitFor();
  assert.match(await page.locator('.audit-summary').innerText(),/Chiusa.*Riaperta/);
  assert.equal(await page.locator('details').isVisible(),true);
  assert.equal(await page.locator('details pre').first().isVisible(),false);
  await page.locator('details summary').click();
  assert.match(await page.locator('details').innerText(),/SESSION_REOPENED.*Closed.*Reopened/s);
  if(process.env.CC_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.CC_SCREENSHOT_DIR,'audit-mobile-offline.png'),fullPage:true});
  await page.goto(base+'/notifications?cc_ops_view=Notifiche');
  const content=page.getByText('Contenuto della conferma');await content.waitFor();await content.click();
  assert.match(await page.locator('.history-entry details').innerText(),/14\/10\/2026.*12:00.*Marco.*Primo incontro.*60 minuti/s);
  assert.equal(await page.locator('.history-entry p').filter({hasText:'<p>'}).count(),0);
  if(process.env.CC_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.CC_SCREENSHOT_DIR,'confirmation-mobile-offline.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',checks:['TS two-column table','TS sections','previous version opens','mobile no overflow','audit Italian states','raw audit collapsed','confirmation content readable','no JavaScript errors'],runtime:'offline mock'}));
 }finally{await browser.close();server.close();}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
