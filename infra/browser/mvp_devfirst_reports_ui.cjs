// Read-only browser verification of the two native accounting reports on the served DEV.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const fixture=JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8'));
const out=process.env.CC_ISSUE137_OUTPUT;
const results=[];
(async()=>{
  const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
  try{
    for(const role of ['f','t']){
      const context=await browser.newContext({locale:'it-IT',acceptDownloads:true,viewport:{width:1440,height:900}});
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',e=>errors.push(e.name));
      try{
        await page.goto(process.env.CC_BASE_URL+'/login?redirect-to=/finanza');
        await page.locator('#login_email').fill(fixture.users[role].name);
        await page.locator('#login_password').fill(fixture.users[role].password);
        await page.getByRole('button',{name:'Continua',exact:true}).click();
        await page.waitForURL(u=>new URL(u).pathname!='/login');
        await page.goto(process.env.CC_BASE_URL+'/finanza');
        await page.getByRole('button',{name:'Report contabili',exact:true}).click();
        await page.locator('#start').fill('2026-01-01');
        await page.locator('#end').fill('2026-12-31');
        await page.locator('#filters button[type=submit]').click();
        for(const [id,name] of [['run-general-ledger','Libro giornale'],['run-trial-balance','Bilancio di verifica']]){
          await page.locator('#'+id).click();
          await page.getByRole('heading',{name,exact:true}).waitFor();
          await page.locator('#native-report-result table tbody').waitFor();
          const rows=await page.locator('#native-report-result table tbody tr').count();
          const headers=await page.locator('#native-report-result th').allTextContents();
          results.push({role,report:id,rows,columns:headers.length,visible:rows>0&&headers.length>0});
          await page.screenshot({path:path.join(out,role+'-'+id+'-desktop.png'),fullPage:true});
        }
        const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-native-report').click()]);
        results.push({role,report:'trial-balance-export',csv:download.suggestedFilename().endsWith('.csv')});
        await page.setViewportSize({width:390,height:844});
        results.push({role,report:'mobile',noOverflow:await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)});
        await page.screenshot({path:path.join(out,role+'-trial-balance-mobile.png'),fullPage:true});
        results.push({role,report:'javascript',errors});
      }finally{await context.close();}
    }
  }finally{await browser.close();}
  fs.writeFileSync(path.join(out,'reports-ui.json'),JSON.stringify({results},null,2));
  console.log(JSON.stringify({results}));
})().catch(e=>{console.error(e.stack);process.exit(2)});
