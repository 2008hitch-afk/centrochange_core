/* Read-only inventory of actual rendered client text. Private output only. */
const fs = require('node:fs');
const {chromium} = require('playwright');

async function collectVisibleText(page) {
  return page.evaluate(() => {
    const root = document.body;
    const visible = element => {
      if (!element || element.closest('[aria-hidden="true"], [inert]')) return false;
      const style = getComputedStyle(element), box = element.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' &&
        Number(style.opacity) !== 0 && box.width > 0 && box.height > 0;
    };
    const items = [], seen = new Set();
    const add = (kind, text) => {
      const value = String(text || '').replace(/\s+/g, ' ').trim();
      if (!value || value.length > 240 || seen.has(kind + ':' + value)) return;
      seen.add(kind + ':' + value);
      items.push({kind, text:value});
    };
    const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    while (walk.nextNode()) {
      const node = walk.currentNode, element = node.parentElement;
      if (!element || /^(SCRIPT|STYLE|NOSCRIPT|OPTION)$/.test(element.tagName) ||
          !visible(element)) continue;
      add('text', node.textContent);
    }
    for (const element of root.querySelectorAll('[placeholder], [title], [aria-label]')) {
      if (!visible(element)) continue;
      for (const attribute of ['placeholder','title','aria-label']) add(attribute, element.getAttribute(attribute));
    }
    for (const select of root.querySelectorAll('select')) {
      if (visible(select)) for (const option of select.options) add('option', option.textContent);
    }
    add('browser-title', document.title);
    return items;
  });
}

async function waitForClient(page) {
  await page.locator('#cc-desk-sidebar').waitFor({timeout:30000});
  await page.waitForFunction(() => document.readyState === 'complete' &&
    !!document.querySelector('.page-wrapper,.layout-main-section,.cc-unified-desk'),
  null, {timeout:12000});
  // Frappe inserts List/Form and Desk content after the document load event.
  // A rendered-text inventory taken before the API work settles is misleading.
  await page.waitForLoadState('networkidle',{timeout:8000});
}

async function run() {
  const fixture = JSON.parse(fs.readFileSync(process.env.CC_DEMO_FIXTURE, 'utf8'));
  const users = (fixture.fixture || fixture).users;
  const output = process.env.CC_INVENTORY_OUTPUT;
  const screenshots = process.env.CC_INVENTORY_SCREENSHOTS;
  if (!output || !users) throw Error('Private fixture and output path required');
  const base = process.env.CC_BASE_URL || 'http://centrochange.local:8082';
  const ip = process.env.CC_BROWSER_IP || '127.0.0.1';
  if (!/^127\.0\.0\.[12]$/.test(ip)) throw Error('Only isolated/local loopback targets permitted');
  const roles = (process.env.CC_INVENTORY_ROLES || 'm,s,a,b,c,f,t').split(',');
  const widths = (process.env.CC_INVENTORY_WIDTHS || '1440,390').split(',').map(Number);
  const scanRoutes = process.env.CC_INVENTORY_ROUTES !== '0';
  const scanForms = process.env.CC_INVENTORY_FORMS !== '0';
  const forms = [['patient','m'],['healthcare-practitioner','m'],['item','m'],
    ['item-price','m'],['appointment-type','m'],['cc-center-service','m'],
    ['cc-package-template','m'],['sales-invoice','m'],['purchase-invoice','f'],
    ['payment-entry','f'],['bank-transaction','f']];
  const browser = await chromium.launch({headless:true,args:[
    `--host-resolver-rules=MAP centrochange.local ${ip}`,'--no-proxy-server','--disable-dev-shm-usage']});
  const rows=[];
  try {
    for (const role of roles) for (const width of widths) {
      if (!users[role]) throw Error('Unknown demo role: '+role);
      const context = await browser.newContext({viewport:{width,height:900},locale:'it-IT',
        timezoneId:'Europe/Rome',serviceWorkers:'block'});
      const page = await context.newPage();
      const errors=[];
      let loginReloads=0;
      page.on('pageerror', error => errors.push(error.message));
      try {
        await page.goto(base+'/login');
        // The isolated clone can finish its first asset warmup after HTTP 200.
        // Record a single recovery reload, then fail if the real login is absent.
        try { await page.locator('#login_email').waitFor({timeout:10000}); }
        catch { loginReloads=1; await page.reload();
          await page.locator('#login_email').waitFor({timeout:20000}); }
        await page.locator('#login_email').fill(users[role].name);
        await page.locator('#login_password').fill(users[role].password);
        await page.getByRole('button',{name:'Continua'}).click();
        await waitForClient(page);
        let links = scanRoutes ? await page.locator('#cc-desk-sidebar a[href]').evaluateAll(anchors =>
          [...new Set(anchors.map(a=>a.getAttribute('href')).filter(h=>h?.startsWith('/app/')))])
          : [];
        if(process.env.CC_INVENTORY_ROUTE_FILTER)
          links=links.filter(h=>process.env.CC_INVENTORY_ROUTE_FILTER.split(',').some(part=>
            part==='@agenda' ? new URL(h,base).searchParams.get('cc_view')==='agenda' &&
              !new URL(h,base).searchParams.has('cc_ops_view') : h.includes(part)));
        for (const href of links) {
          try {
            await page.goto(base+href,{waitUntil:'load',timeout:30000});
            await waitForClient(page);
            rows.push({role,width,screen:href,state:'ready',items:await collectVisibleText(page)});
            if (screenshots && role==='m' && new URL(href,base).searchParams.get('cc_view')==='agenda' &&
                !new URL(href,base).searchParams.has('cc_ops_view'))
              await page.screenshot({path:`${screenshots}/agenda-${width}.png`,fullPage:true,animations:'disabled'});
            // The audit and operational pages keep canonical technical data
            // under native <details>. Inspect a bounded sample separately so
            // its labels are reviewed without confusing it with the main UI.
            const details=page.locator('details > summary');
            let expanded=0;
            for(let i=0;i<Math.min(await details.count(),8);i++) {
              const item=details.nth(i);
              if(await item.isVisible()) {
                try {await item.click({timeout:3000});expanded++;}
                catch { /* A collapsed native panel may be replaced asynchronously. */ }
              }
            }
            if(expanded) rows.push({role,width,screen:href,state:'advanced',
              items:await collectVisibleText(page)});
          } catch(error) { rows.push({role,width,screen:href,state:'ERROR',error:String(error.message).slice(0,200)}); }
        }
        for (const [doctype,owner] of (scanForms ? forms : []).filter(([doctype,owner])=>
          owner===role && (!process.env.CC_INVENTORY_FORM_FILTER ||
            process.env.CC_INVENTORY_FORM_FILTER.split(',').includes(doctype)))) {
          const route='/app/'+doctype;
          try {
            await page.goto(base+route,{waitUntil:'load',timeout:30000});
            await page.locator('.list-row .list-subject a').first().click();
            await page.waitForFunction(()=>window.cur_frm?.doc?.name && document.querySelector('.form-layout'));
            if(['sales-invoice','purchase-invoice'].includes(doctype) &&
                await page.evaluate(()=>Boolean(window.cur_frm?.doc?.in_words &&
                  window.cur_frm?.doc?.currency==='EUR')))
              await page.locator('.cc-invoice-words').waitFor({timeout:12000});
            rows.push({role,width,screen:route+'/FORM',state:'main',items:await collectVisibleText(page)});
            if (screenshots && width===1440 &&
                ['patient','healthcare-practitioner','sales-invoice','purchase-invoice'].includes(doctype))
              await page.screenshot({path:`${screenshots}/${doctype}-${role}.png`,fullPage:true,animations:'disabled'});
            const sections=page.locator('.form-layout .section-head.collapsed');
            for (let i=0;i<Math.min(await sections.count(),20);i++) {
              if (await sections.nth(i).isVisible()) await sections.nth(i).click({timeout:3000}).catch(()=>{});
            }
            rows.push({role,width,screen:route+'/FORM',state:'sections',items:await collectVisibleText(page)});
            const tabs=page.locator('.form-tabs .nav-link');
            for(let i=0;i<Math.min(await tabs.count(),12);i++) {
              const tab=tabs.nth(i);
              if(!await tab.isVisible())continue;
              const label=(await tab.innerText()).trim();
              await tab.click({timeout:3000}).catch(()=>{});
              rows.push({role,width,screen:route+'/FORM',state:'tab:'+label,
                items:await collectVisibleText(page)});
            }
          } catch(error) { rows.push({role,width,screen:route+'/FORM',state:'ERROR',error:String(error.message).slice(0,200)}); }
        }
      } catch(error) { rows.push({role,width,screen:'login',state:'ERROR',error:String(error.message).slice(0,200)}); }
      rows.push({role,width,screen:'javascript',state:errors.length?'ERROR':'ready',errors:errors.slice(0,5),
        loginReloads});
      await context.close();
      fs.writeFileSync(output,JSON.stringify(rows,null,2),{mode:0o600});
    }
  } finally { await browser.close(); }
  fs.writeFileSync(output,JSON.stringify(rows,null,2),{mode:0o600});
  const unique=new Set(rows.flatMap(row=>(row.items||[]).map(item=>item.text)));
  console.log(JSON.stringify({screens:rows.filter(row=>row.items).length,
    errors:rows.filter(row=>row.state==='ERROR').length,uniqueText:unique.size}));
  if(rows.some(row=>row.state==='ERROR'))process.exitCode=1;
}

module.exports={collectVisibleText};
if(require.main===module)run().catch(error=>{console.error(String(error.message));process.exitCode=1});
