/* Read-only human invoice print/PDF probe; never stores document contents. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const fixture=JSON.parse(fs.readFileSync(process.env.CC_DEMO_FIXTURE,'utf8'));
const users=(fixture.fixture||fixture).users;
const base=process.env.CC_BASE_URL||'http://centrochange.local:8082';
const output=process.env.CC_LOCALE_OUTPUT;
const role=process.env.CC_PRINT_ROLE||'f';
if(!output||!users?.[role])throw Error('Private fixture/output required');
async function main(){
  const browser=await chromium.launch({headless:true,args:[
    '--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
  try{
    const context=await browser.newContext({locale:'it-IT',timezoneId:'Europe/Rome',serviceWorkers:'block'});
    const page=await context.newPage();
    await page.goto(base+'/login');
    await page.locator('#login_email').fill(users[role].name);
    await page.locator('#login_password').fill(users[role].password);
    await page.getByRole('button',{name:'Continua'}).click();
    await page.locator('#cc-desk-sidebar').waitFor();
    await page.goto(base+'/app/sales-invoice');
    await page.locator('.list-row .list-subject a').first().waitFor();
    const links=await page.locator('.list-row .list-subject a').evaluateAll(anchors=>anchors.slice(0,15).map(a=>a.href));
    let name,selectedStatus;
    for(const link of links){
      await page.goto(link);
      await page.waitForFunction(()=>window.cur_frm?.doc?.name);
      const doc=await page.evaluate(()=>({name:window.cur_frm.doc.name,status:window.cur_frm.doc.docstatus}));
      if(doc.status===1){name=doc.name;selectedStatus=doc.status;break;}
    }
    if(!name)throw Error('No submitted synthetic invoice found in the first 15 list rows');
    const result={role,selectedStatus,views:[]};
    for(const suffix of ['', '&_lang=it']){
      const print=await page.goto(base+'/printview?doctype=Sales%20Invoice&name='+encodeURIComponent(name)+suffix);
      const text=await page.locator('body').innerText();
      result.views.push({explicitItalian:Boolean(suffix),status:print.status(),pageTitle:await page.title(),
        english:['Sales Invoice','Billed To','Subtotal','EUR One Hundred only.','No.','Nos 1']
          .filter(s=>text.includes(s)),
        europeanDate:/\b\d{2}\/\d{2}\/\d{4}\b/.test(text),
        isoDate:/\b20\d{2}-\d{2}-\d{2}\b/.test(text),
        amPm:/\b\d{1,2}:\d{2}\s?(?:AM|PM)\b/i.test(text)});
      await page.screenshot({path:path.join(output,suffix?'invoice-print-it.png':'invoice-print.png'),fullPage:true,animations:'disabled'});
    }
    const pdf=await page.evaluate(async name=>{
      const url='/api/method/frappe.utils.print_format.download_pdf?doctype=Sales%20Invoice&name='+encodeURIComponent(name)+'&language=it';
      const response=await fetch(url),buffer=await response.arrayBuffer();
      const bytes=new Uint8Array(buffer);
      let exception=null,cause=null;
      if(!response.ok){try{
        const payload=JSON.parse(new TextDecoder().decode(bytes));
        exception=payload.exc_type||null;
        let trace=String(payload.exc||'');
        try{trace=JSON.parse(trace).join('\n')}catch{}
        const offset=trace.lastIndexOf('OSError:');
        cause=(offset>=0?trace.slice(offset,offset+450):'')
          .replace(/(?:password|token|secret)\S*/gi,'[REDACTED]');
      }catch{}}
      return {status:response.status,type:response.headers.get('content-type'),exception,cause,
        pdf:String.fromCharCode(...bytes.slice(0,5))==='%PDF-',bytes:bytes.length};
    },name);
    result.pdf=pdf;
    fs.writeFileSync(path.join(output,'documents-post.json'),JSON.stringify(result,null,2));
    console.log(JSON.stringify(result));
    await context.close();
    if(result.views.some(v=>v.status!==200||v.english.length)||pdf.status!==200||!pdf.pdf)process.exitCode=1;
  }finally{await browser.close()}
}
main().catch(e=>{console.error(String(e.stack));process.exitCode=1});
