// Offline browser contract for the #81 path. API responses are synthetic; no DEV request.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const http=require('node:http');
const path=require('node:path');
const {chromium}=require('playwright');

const root=path.resolve(__dirname,'../../app/centrochange_core/centrochange_core/public/js');
const fragmentSource=fs.readFileSync(path.join(root,'cc_desk_fragments.js'),'utf8');
const fragments=JSON.parse(fragmentSource.slice(fragmentSource.indexOf('{')).trim().replace(/;$/,''));
const responses={
  'reporting.bootstrap':write=>({centers:[{name:'CENTRO-A',branch:'Centro A'}],center:'CENTRO-A',can_write:write,is_manager:false,
    practitioners:[{name:'PRAC-ALFA',practitioner_name:'Professionista Alfa',supplier:'SUP-ALFA'}],items:[],accounts:[]}),
  'reporting.summary':()=>({totals:{revenue_net:0,collected:0,receivable_outstanding:0,purchase_net:0,payable_outstanding:0,expected_compensation:40,
    sessions:1,unresolved_expectations:0},sales_invoices:[],purchase_invoices:[],exceptions:[]}),
  'reporting.records':(_,query)=>query.get('doctype')==='CC Professional Expectation'
    ?[{name:'CANONICAL-EXP-1',appointment:'CANONICAL-SESSION-1',appointment_label:'2026-10-13 · Paziente Alfa',practitioner:'PRAC-ALFA',state:'OK',amount:40,amount_known:1}]
    :[{name:'CANONICAL-PI-1',docstatus:1,supplier:'SUP-ALFA',grand_total:40,outstanding_amount:40}]
};
let writable=true;
const writes=[];
const server=http.createServer((request,response)=>{
  const url=new URL(request.url,'http://localhost');
  if(url.pathname==='/test'){
    response.setHeader('Content-Type','text/html; charset=utf-8');
    response.end('<!doctype html><html lang="it"><head><meta name="csrf-token" content="synthetic"></head><body class="finance-page"><nav id="navigation"></nav><button id="logout"></button><div class="workspace">'+fragments.finance.page+'</div>'+fragments.finance.modal+'<script type="module" src="/assets/centrochange_core/js/finance_workspace.js"></script></body></html>');
  }else if(url.pathname.startsWith('/assets/centrochange_core/js/')){
    const name=path.basename(url.pathname);response.setHeader('Content-Type','text/javascript');response.end(fs.readFileSync(path.join(root,name)));
  }else if(url.pathname.startsWith('/api/method/')){
    const method=url.pathname.split('.').slice(-2).join('.');
    if(request.method==='POST'){
      let body='';request.on('data',chunk=>body+=chunk);request.on('end',()=>{
        writes.push({method,args:JSON.parse(body)});response.setHeader('Content-Type','application/json');
        response.end(JSON.stringify({message:{name:'CANONICAL-COMPARISON-1',state:'REVIEW'}}));
      });return;
    }
    const handler=responses[method];response.setHeader('Content-Type','application/json');
    if(!handler){response.statusCode=404;response.end(JSON.stringify({message:'Unexpected API'}));return;}
    response.end(JSON.stringify({message:handler(writable,url.searchParams)}));
  }else{response.statusCode=404;response.end('Missing');}
});
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({headless:true,executablePath:process.env.CC_CHROMIUM});
  try{
    const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/test`);
    const entry=page.getByRole('button',{name:'Confronta fattura professionista'});
    await entry.waitFor();await entry.click();
    await page.getByRole('heading',{name:'Confronta atteso e ricevuto'}).waitFor();
    const snapshot=page.locator('#modal [name=expectations] option');
    assert.equal(await snapshot.count(),1);
    assert.equal(await snapshot.getAttribute('value'),'CANONICAL-EXP-1');
    assert.match(await snapshot.innerText(),/Paziente Alfa.*Professionista Alfa.*40,00.*Confermato/);
    assert.equal(await page.locator('#modal [name=purchase_invoice] option[value="CANONICAL-PI-1"]').count(),1);
    await page.locator('#modal [name=purchase_invoice]').selectOption('CANONICAL-PI-1');
    await page.locator('#modal [name=expectations]').selectOption('CANONICAL-EXP-1');
    await page.locator('#modal [name=reason]').fill('Confronto sintetico');
    await page.locator('#modal-submit').click();
    await page.getByText('Operazione registrata.').waitFor();
    assert.deepEqual(writes,[{method:'professional_economics.compare',args:{purchase_invoice:'CANONICAL-PI-1',expectations:['CANONICAL-EXP-1'],reason:'Confronto sintetico'}}]);
    assert.deepEqual(errors,[]);
    writable=false;await page.goto(`http://127.0.0.1:${server.address().port}/test`);
    await page.getByText('Contabilità del centro').waitFor();
    assert.equal(await entry.count(),0,'read-only role must not see comparison action');
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({status:'PASS',checks:['summary entry','canonical snapshot value','human snapshot label','exact comparison API payload','read-only action hidden','no JavaScript errors'],runtime:'offline mock'}));
  }finally{await browser.close();server.close();}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
