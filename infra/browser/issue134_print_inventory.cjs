/* Actual invoice HTML and PDF inventory on loopback only; private files. */
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

async function run() {
  const fixture = JSON.parse(fs.readFileSync(process.env.CC_DEMO_FIXTURE, 'utf8'));
  const users = (fixture.fixture || fixture).users;
  const output = process.env.CC_INVENTORY_OUTPUT;
  const ip = process.env.CC_BROWSER_IP || '127.0.0.2';
  if (!/^127\.0\.0\.[12]$/.test(ip) || !output || !users?.f)
    throw Error('Private loopback fixture and output required');
  const base = 'http://centrochange.local:8082';
  const browser = await chromium.launch({headless:true,args:[
    `--host-resolver-rules=MAP centrochange.local ${ip}`,
    '--no-proxy-server','--disable-dev-shm-usage']});
  try {
    const context = await browser.newContext({locale:'it-IT',timezoneId:'Europe/Rome',serviceWorkers:'block'});
    const page = await context.newPage();
    await page.goto(base+'/login');
    try { await page.locator('#login_email').waitFor({timeout:10000}); }
    catch {
      fs.writeFileSync(path.join(output,'initial-login.html'),await page.content(),{mode:0o600});
      await page.reload();
      await page.locator('#login_email').waitFor({timeout:20000});
    }
    await page.locator('#login_email').fill(users.f.name);
    await page.locator('#login_password').fill(users.f.password);
    await page.getByRole('button',{name:'Continua'}).click();
    await page.locator('#cc-desk-sidebar').waitFor();
    await page.goto(base+'/app/sales-invoice');
    await page.locator('.list-row .list-subject a').first().waitFor();
    const links = await page.locator('.list-row .list-subject a').evaluateAll(
      anchors => anchors.slice(0,20).map(a=>a.href));
    let name;
    for (const link of links) {
      await page.goto(link);
      await page.waitForFunction(()=>window.cur_frm?.doc?.name);
      const doc = await page.evaluate(()=>({name:cur_frm.doc.name,status:cur_frm.doc.docstatus}));
      if (doc.status===1) {name=doc.name;break;}
    }
    if (!name) throw Error('No submitted synthetic invoice for print inventory');
    const htmlResponse = await page.goto(base+'/printview?doctype=Sales%20Invoice&name='+encodeURIComponent(name)+'&_lang=it');
    const html = {status:htmlResponse.status(),title:await page.title(),
      text:await page.locator('body').innerText()};
    fs.writeFileSync(path.join(output,'invoice.html'),await page.content(),{mode:0o600});
    await page.screenshot({path:path.join(output,'invoice.png'),fullPage:true,animations:'disabled'});
    // Fetch inside Chromium: Node's request client does not inherit Chrome's
    // isolated host-resolver rule for centrochange.local.
    const result = await page.evaluate(async name => {
      const response = await fetch('/api/method/frappe.utils.print_format.download_pdf?doctype=Sales%20Invoice&name='+encodeURIComponent(name)+'&language=it');
      const bytes = new Uint8Array(await response.arrayBuffer());
      let binary=''; for (const byte of bytes) binary+=String.fromCharCode(byte);
      return {status:response.status,contentType:response.headers.get('content-type'),data:btoa(binary)};
    },name);
    const bytes = Buffer.from(result.data,'base64');
    const pdf = {status:result.status,contentType:result.contentType,
      signature:bytes.subarray(0,5).toString('ascii'),length:bytes.length};
    if (pdf.status===200 && pdf.signature==='%PDF-')
      fs.writeFileSync(path.join(output,'invoice.pdf'),bytes,{mode:0o600});
    fs.writeFileSync(path.join(output,'print-inventory.json'),JSON.stringify({html,pdf},null,2),{mode:0o600});
    console.log(JSON.stringify({htmlStatus:html.status,pdfStatus:pdf.status,pdfSignature:pdf.signature,
      htmlTitle:html.title}));
    await context.close();
    if(html.status!==200||pdf.status!==200||pdf.signature!=='%PDF-')process.exitCode=1;
  } finally { await browser.close(); }
}
run().catch(error=>{console.error(String(error.message));process.exitCode=1});
