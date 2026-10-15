// #139 W1 read-only native List/Form renderer check on the actually served DEV.
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const {assetResponseError} = require('./issue139_asset_response.cjs');

const fixture = JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE, 'utf8'));
const user = (fixture.fixture || fixture).users.m;
const out = process.env.CC_ISSUE137_OUTPUT;
const base = process.env.CC_BASE_URL || 'http://centrochange.local:8082';
const width = Number(process.env.CC_ISSUE137_WIDTH || 1440);
if (!user || !out || ![390, 1440].includes(width)) throw Error('Private fixture/output and supported viewport required');
fs.mkdirSync(out, {recursive: true, mode: 0o700});
const routes = ['patient','healthcare-practitioner','sales-invoice','purchase-invoice','payment-entry',
  'bank-transaction','item','item-price','appointment-type','cc-center-service','cc-package-template'];
const endpoint = url => {const u = new URL(url, base); return u.pathname;};

async function geometry(page, kind) {
  return page.evaluate(kind => {
    const visible = el => {const r=el.getBoundingClientRect(), s=getComputedStyle(el);
      return r.width>1 && r.height>1 && s.display!=='none' && s.visibility!=='hidden';};
    const icons=[...document.querySelectorAll('svg,.icon')].filter(visible);
    const target=kind==='list'?document.querySelector('.list-row-container,.listview-body'):
      document.querySelector('.form-page');
    const clippedBadges=kind==='list'?[...document.querySelectorAll('.list-row-container .es-badge')]
      .filter(visible).filter(badge=>{
        const b=badge.getBoundingClientRect();
        for(let parent=badge.parentElement;parent;parent=parent.parentElement){
          const style=getComputedStyle(parent);
          if(!['hidden','clip'].includes(style.overflowX)) continue;
          const r=parent.getBoundingClientRect();
          if(b.left<r.left-2||b.right>r.right+2) return true;
        }
        return false;
      }).length:0;
    return {targetVisible:!!target && visible(target),
      clippedBadges,
      maxIconPx:Math.round(Math.max(0,...icons.map(x=>{const r=x.getBoundingClientRect();return Math.max(r.width,r.height)}))),
      overflowPx:Math.max(0,document.documentElement.scrollWidth-innerWidth),
      stylesheets:document.styleSheets.length,
      deskStyle:[...document.styleSheets].some(s=>/\/desk\.bundle\.[A-Z0-9]+\.css/.test(s.href||'')),
      erpStyle:[...document.styleSheets].some(s=>/\/erpnext\.bundle\.[A-Z0-9]+\.css/.test(s.href||''))};
  }, kind);
}

(async()=>{
  const browserIp=process.env.CC_ISSUE139_BROWSER_IP || '127.0.0.1';
  if (!['127.0.0.1','127.0.0.2'].includes(browserIp)) throw Error('Unsupported browser loopback target');
  const browser=await chromium.launch({headless:true,args:[
    `--host-resolver-rules=MAP centrochange.local ${browserIp}`,'--no-proxy-server','--disable-dev-shm-usage']});
  const context=await browser.newContext({viewport:{width,height:width===390?844:900},
    locale:'it-IT',timezoneId:'Europe/Rome',serviceWorkers:'block'});
  const page=await context.newPage();
  const results=[];
  try {
    await page.goto(base+'/login');
    await page.locator('#login_email').fill(user.name);
    await page.locator('#login_password').fill(user.password);
    await page.getByRole('button',{name:'Continua'}).click();
    await page.locator('#cc-desk-sidebar').waitFor();
    for(const route of routes) {
      const cssErrors=[],jsErrors=[],otherConsole=[];
      const onResponse=response=>{
        const p=endpoint(response.url());
        if(!/\.(css|js)$/.test(p)) return;
        const problem=assetResponseError(response,p.endsWith('.css')?'css':'js');
        if(problem) (p.endsWith('.css')?cssErrors:jsErrors).push({path:p,...problem});
      };
      const onError=e=>otherConsole.push(String(e.message).slice(0,220));
      const onConsole=m=>{if(m.type()==='error')otherConsole.push(m.text().slice(0,220));};
      page.on('response',onResponse);page.on('pageerror',onError);page.on('console',onConsole);
      let list=null,form=null,reason=[];
      try {
        await page.goto(base+'/app/'+route,{waitUntil:'domcontentloaded',timeout:30000});
        await page.waitForTimeout(950);
        list=await geometry(page,'list');
        await page.screenshot({path:path.join(out,`w1-${width}-${route}-list.png`),
          fullPage:true,animations:'disabled'});
        const first=page.locator('.list-row .list-subject a,.list-row .level-left a[href]').first();
        if(!await first.count()) reason.push('NO_FIRST_RECORD');
        else {
          await first.click({timeout:6000});await page.waitForTimeout(850);
          form=await geometry(page,'form');
          await page.screenshot({path:path.join(out,`w1-${width}-${route}-form.png`),
            fullPage:true,animations:'disabled'});
        }
      } catch(e) {reason.push('NAVIGATION_OR_CAPTURE');otherConsole.push(String(e.message).slice(0,220));}
      for(const [kind,metric] of [['LIST',list],['FORM',form]]) {
        if(!metric?.targetVisible) reason.push(kind+'_MISSING');
        if(metric?.maxIconPx>96) reason.push(kind+'_OVERSIZED_ICONS');
        if(metric?.overflowPx>3) reason.push(kind+'_HORIZONTAL_OVERFLOW');
        if(kind==='LIST' && metric?.clippedBadges) reason.push('LIST_CLIPPED_BADGES');
        if(!metric?.deskStyle || !metric?.erpStyle) reason.push(kind+'_CORE_CSS_MISSING');
      }
      if(cssErrors.length||jsErrors.length) reason.push('BUNDLE_HTTP_OR_MIME');
      page.off('response',onResponse);page.off('pageerror',onError);page.off('console',onConsole);
      results.push({route,status:reason.length?'FAIL':'PASS',reason,list,form,cssErrors,jsErrors,
        consoleErrors:otherConsole});
      console.error(`${width} ${route}: ${reason.length?'FAIL '+reason.join(','):'PASS'}`);
    }
    const summary={pass:results.filter(r=>r.status==='PASS').length,
      fail:results.filter(r=>r.status==='FAIL').length};
    fs.writeFileSync(path.join(out,`issue139-native-${width}.json`),JSON.stringify({width,results,summary},null,2));
    console.log(JSON.stringify({width,summary}));
    if(summary.fail)process.exitCode=2;
  } finally {await browser.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
