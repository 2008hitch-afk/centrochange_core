/* Read-only second pass over visible native Form text, including help and activity. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.CC_BASE_URL||'http://centrochange.local:8082';
const fixture=JSON.parse(fs.readFileSync(process.env.CC_DEMO_FIXTURE,'utf8'));
const users=(fixture.fixture||fixture).users;
const output=process.env.CC_LOCALE_OUTPUT;
if(!output||!users?.m||!users?.f)throw Error('Private fixture/output required');
fs.mkdirSync(output,{recursive:true,mode:0o700});
const routes=[['patient','m'],['healthcare-practitioner','m'],['item','m'],['item-price','m'],
  ['appointment-type','m'],['cc-center-service','m'],['cc-package-template','m'],
  ['sales-invoice','m'],['purchase-invoice','f'],['payment-entry','f'],['bank-transaction','f']];
const patterns={
  activity:/\b(?:Last Edited By|Created By|Edited By|Assigned To)\b/i,
  nativeHelp:/\b(?:Issue a debit note|Issue a credit note|Get Items From|No results|Required|Mandatory|Click to add)\b/i,
  timeSeconds:/\b\d{2}:\d{2}:\d{2}\b/,
  amPm:/\b\d{1,2}:\d{2}\s?(?:AM|PM)\b/i,
};
async function login(page,user){
  await page.goto(base+'/login',{waitUntil:'domcontentloaded'});
  await page.locator('#login_email').fill(user.name);
  await page.locator('#login_password').fill(user.password);
  await page.getByRole('button',{name:'Continua'}).click();
  await page.locator('#cc-desk-sidebar').waitFor({timeout:30000});
}
async function main(){
  const browser=await chromium.launch({headless:true,args:[
    '--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
  const rows=[];
  try{
    for(const role of ['m','f']){
      const context=await browser.newContext({viewport:{width:1440,height:900},locale:'it-IT',timezoneId:'Europe/Rome',serviceWorkers:'block'});
      const page=await context.newPage();
      await login(page,users[role]);
      for(const [route,owner] of routes.filter(([,owner])=>owner===role)){
        try{
          await page.goto(base+'/app/'+route,{waitUntil:'domcontentloaded'});
          await page.locator('.list-row .list-subject a').first().click();
          await page.waitForFunction(()=>window.cur_frm?.doc?.name&&document.querySelector('.form-layout'));
          if(['sales-invoice','purchase-invoice','payment-entry','bank-transaction'].includes(route))
            await page.locator('.cc-finance-context').waitFor({timeout:15000});
          const matches=await page.evaluate(source=>{
            const text=document.body.innerText;
            const lines=text.split('\n').map(x=>x.trim()).filter(Boolean);
            return Object.fromEntries(Object.entries(source).map(([key,pattern])=>{
              const re=new RegExp(pattern,'i');
              // Report matching text only for bounded, nonclinical phrases.
              return [key,lines.filter(line=>re.test(line)).map(line=>line.slice(0,140)).slice(0,5)];
            }));
          },Object.fromEntries(Object.entries(patterns).map(([k,v])=>[k,v.source])));
          rows.push({route,role,status:'PASS',matches});
          if(['sales-invoice','purchase-invoice'].includes(route))
            await page.screenshot({path:path.join(output,`settled-${route}-${role}.png`),animations:'disabled'});
        }catch(e){rows.push({route,role,status:'FAIL',reason:String(e.message).slice(0,180)});}
      }
      await context.close();
    }
  }finally{await browser.close()}
  fs.writeFileSync(path.join(output,'native-residual.json'),JSON.stringify(rows,null,2));
  console.log(JSON.stringify({forms:rows.length,failures:rows.filter(x=>x.status==='FAIL').length,
    matched:rows.filter(x=>Object.values(x.matches||{}).some(values=>values.length))
      .map(({route,matches})=>({route,kinds:Object.fromEntries(Object.entries(matches).map(([k,v])=>[k,v.length]))}))}));
  if(rows.some(x=>x.status==='FAIL'))process.exitCode=1;
}
main().catch(e=>{console.error(String(e.stack));process.exitCode=1});
