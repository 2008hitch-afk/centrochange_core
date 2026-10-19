// A single tagged, synthetic incoming document exercises the real attachment form.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const fixture=JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8'));
const tag=process.env.CC_MVP_ATTACHMENT_TAG;
if(!/^CC-MVP-ATT-[0-9a-f]{10}$/.test(tag||''))throw new Error('Unsafe attachment fixture tag');
const output=process.env.CC_ISSUE137_OUTPUT;
const xml=`<?xml version="1.0" encoding="UTF-8"?><FatturaElettronica versione="FPR12"><FatturaElettronicaHeader><CedentePrestatore><DatiAnagrafici><IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>SYNTHETIC-${tag}</IdCodice></IdFiscaleIVA><Anagrafica><Denominazione>SYNTHETIC PROVIDER</Denominazione></Anagrafica></DatiAnagrafici></CedentePrestatore><CessionarioCommittente><DatiAnagrafici><IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>00000000000</IdCodice></IdFiscaleIVA></DatiAnagrafici></CessionarioCommittente></FatturaElettronicaHeader><FatturaElettronicaBody><DatiGenerali><DatiGeneraliDocumento><TipoDocumento>TD01</TipoDocumento><Divisa>EUR</Divisa><Data>2026-10-19</Data><Numero>${tag}</Numero><ImportoTotaleDocumento>100</ImportoTotaleDocumento></DatiGeneraliDocumento></DatiGenerali><DatiBeniServizi><DettaglioLinee><NumeroLinea>1</NumeroLinea><Descrizione>SYNTHETIC administrative attachment test</Descrizione><Quantita>1</Quantita><PrezzoUnitario>100</PrezzoUnitario><PrezzoTotale>100</PrezzoTotale><AliquotaIVA>0</AliquotaIVA></DettaglioLinee><DatiRiepilogo><AliquotaIVA>0</AliquotaIVA><ImponibileImporto>100</ImponibileImporto><Imposta>0</Imposta></DatiRiepilogo></DatiBeniServizi></FatturaElettronicaBody></FatturaElettronica>`;
function syntheticPdf(label){
  const stream=`BT /F1 10 Tf 20 250 Td (${label}) Tj ET\n`;
  const objects=[
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
    `<< /Length ${Buffer.byteLength(stream)} >>\nstream\n${stream}endstream`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'
  ];
  let body='%PDF-1.4\n',offsets=[0];
  for(let i=0;i<objects.length;i++){offsets.push(Buffer.byteLength(body));body+=`${i+1} 0 obj\n${objects[i]}\nendobj\n`;}
  const start=Buffer.byteLength(body);
  body+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n`;
  for(const offset of offsets.slice(1))body+=`${String(offset).padStart(10,'0')} 00000 n \n`;
  body+=`trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${start}\n%%EOF\n`;
  return Buffer.from(body);
}
const pdf=syntheticPdf('Synthetic attachment '+tag);
const checks=[];
let stage='startup';
(async()=>{
  const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
  let privateUrl,sourceName;
  try{
    for(const role of ['f','t','a']){
      const context=await browser.newContext({locale:'it-IT',viewport:{width:role==='t'?390:1440,height:900}}),page=await context.newPage();
      try{
        stage=role+':login';
        await page.goto(process.env.CC_BASE_URL+'/login?redirect-to=/finanza');
        await page.locator('#login_email').fill(fixture.users[role].name);
        await page.locator('#login_password').fill(fixture.users[role].password);
        await page.getByRole('button',{name:'Continua',exact:true}).click();
        await page.waitForURL(u=>new URL(u).pathname!='/login');
        if(role==='f'){
          stage='f:open-incoming';
          await page.goto(process.env.CC_BASE_URL+'/finanza');
          await page.getByRole('button',{name:'XML ricevuti',exact:true}).click();
          stage='f:intake-form';
          await page.locator('#finance-action').click();
          await page.locator('#modal [name=file]').setInputFiles({name:tag+'.xml',mimeType:'application/xml',buffer:Buffer.from(xml)});
          await page.locator('#modal [name=reason]').fill(tag);
          await page.locator('#modal-submit').click();
          stage='f:intake-save';
          await page.locator('#modal').waitFor({state:'hidden'});
          stage='f:source-row';
          const row=page.locator('#finance-content tr[data-name]').filter({hasText:tag});
          await row.waitFor();
          await row.click();
          stage='f:attachment-upload';
          const upload=await page.evaluate(async ({tag,pdf})=>{
            const source=await fetch('/api/method/centrochange_core.finance.reporting.records?'+new URLSearchParams({center:document.querySelector('#center').value,doctype:'CC Incoming Invoice'})).then(r=>r.json());
            const found=source.message.find(row=>row.invoice_number===tag);
            if(!found)throw new Error('Synthetic source unavailable');
            const response=await fetch('/api/method/centrochange_core.finance.attachments.attach',{method:'POST',credentials:'same-origin',
              headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},
              body:JSON.stringify({doctype:'CC Incoming Invoice',name:found.name,file_name:tag+'.pdf',content_base64:pdf,reason:tag})});
            return {status:response.status,body:await response.json(),name:found.name};
          },{tag,pdf:pdf.toString('base64')});
          if(upload.status!==200||!upload.body.message?.private)throw new Error('Private upload rejected: '+upload.status+' '+String(upload.body.exc_type||'unknown').slice(0,80)+' '+String(upload.body.exception||'').split('\\n').at(-1).slice(0,100));
          sourceName=upload.name;
          stage='f:attachment-save';
          privateUrl=upload.body.message.file_url;
          if(!privateUrl.startsWith('/private/files/'))throw new Error('Attachment is not private');
          checks.push({role,step:'create-and-associate',pass:true});
          const ownDownload=await page.evaluate(async url=>{const r=await fetch(url);return {status:r.status,bytes:(await r.arrayBuffer()).byteLength};},privateUrl);
          checks.push({role,step:'private-file-download',status:ownDownload.status,bytes:ownDownload.bytes,pass:ownDownload.status===200&&ownDownload.bytes===pdf.length});
          await page.reload();
          stage='f:refresh';
          await page.getByRole('button',{name:'XML ricevuti',exact:true}).click();
          await page.locator('#finance-content tr[data-name]').filter({hasText:tag}).click();
          const saved=await page.evaluate(async name=>{const r=await fetch('/api/method/centrochange_core.finance.attachments.list_for_document?'+new URLSearchParams({doctype:'CC Incoming Invoice',name}));return {status:r.status,rows:(await r.json()).message||[]};},upload.name);
          checks.push({role,step:'persist-after-refresh',pass:saved.status===200&&saved.rows.some(row=>row.file_name.startsWith(tag)&&row.file_name.endsWith('.pdf')&&row.file_url===privateUrl)});
        }else if(role==='t'){
          stage='t:read-detail';
          const saved=await page.evaluate(async name=>{const r=await fetch('/api/method/centrochange_core.finance.attachments.list_for_document?'+new URLSearchParams({doctype:'CC Incoming Invoice',name}));return {status:r.status,rows:(await r.json()).message||[]};},sourceName);
          checks.push({role,step:'read-only-detail',pass:saved.status===200&&saved.rows.some(row=>row.file_name.startsWith(tag)&&row.file_name.endsWith('.pdf')&&row.file_url===privateUrl)});
        }else{
          stage='a:denied';
          const denied=await page.evaluate(async center=>{const r=await fetch('/api/method/centrochange_core.finance.reporting.records?'+new URLSearchParams({center,doctype:'CC Incoming Invoice'}));return r.status;},fixture.centers[0]);
          checks.push({role,step:'finance-list-denied',pass:denied===403,status:denied});
        }
        if(privateUrl&&role!=='f'){
          const read=await page.evaluate(async url=>{const r=await fetch(url);return {status:r.status,bytes:(await r.arrayBuffer()).byteLength};},privateUrl);
          checks.push({role,step:'private-file-download',status:read.status,bytes:read.bytes,
            pass:role==='a'?read.status===403:read.status===200&&read.bytes===pdf.length});
        }
      }finally{await context.close();}
    }
  }finally{await browser.close();}
  fs.writeFileSync(path.join(output,'attachment-live.json'),JSON.stringify({checks},null,2));
  console.log(JSON.stringify({status:checks.every(c=>c.pass)?'PASS':'FAIL',checks}));
  if(checks.some(c=>!c.pass))process.exitCode=2;
})().catch(e=>{const detail=String(e.message||'').replace(/(?:password|token|secret)[^\s]*/ig,'[REDACTED]').slice(0,250);fs.writeFileSync(path.join(output,'attachment-live-error.json'),JSON.stringify({errorType:e.name,stage,detail}));console.error(e.name+':'+stage);process.exit(2)});
