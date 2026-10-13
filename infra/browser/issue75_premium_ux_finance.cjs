// Read-only finance UX checks on the existing synthetic DEV documents.
const {chromium}=require("playwright"),assert=require("node:assert/strict"),fs=require("node:fs");
const users=JSON.parse(fs.readFileSync("/qa-fixture.json")).fixture.users;
const base="http://centrochange.local:8080",center="CC-HTTP-UAT0000001 A";
const invoices=[
  ["draft","ACC-SINV-2026-00004","Bozza"],
  ["unpaid","ACC-SINV-2026-00003","Contabilizzata"],
  ["paid","ACC-SINV-2026-00002","Saldata"],
  ["partial","ACC-SINV-2026-00001","Parzialmente saldata"]
];
async function login(page,role){await page.goto(base+"/login");await page.locator("#login_email").fill(users[role].name);await page.locator("#login_password").fill(users[role].password);await page.locator(".form-login button[type=submit]").click();await page.locator("#cc-desk-sidebar").waitFor({timeout:45000});}
(async()=>{
 const browser=await chromium.launch({args:["--host-resolver-rules=MAP centrochange.local 127.0.0.1","--no-proxy-server","--disable-dev-shm-usage"]}),results={};
 for(const role of ["m","f","t"]){
  const context=await browser.newContext({viewport:{width:1440,height:900},locale:"it-IT",serviceWorkers:"block"}),page=await context.newPage(),errors=[];page.on("pageerror",e=>errors.push(e.message));
  await login(page,role);
  await page.goto(base+"/app/cc-unified-desk?cc_view=finance&cc_fin_view=Fatture%20pazienti");
  await page.locator("#center").waitFor({timeout:45000});
  await page.locator("#center").selectOption(center);
  await page.locator('#finance-content tr[data-name="ACC-SINV-2026-00004"]').waitFor({timeout:30000});
  results[role]={invoices:[],errors};
  for(const [slug,name,status] of invoices){
   await page.locator('#finance-content tr[data-name="'+name+'"]').click();
   await page.locator("#detail").waitFor({state:"visible",timeout:30000});
   await page.waitForFunction(name=>document.querySelector("#detail")?.innerText?.includes(name),name);
   const details=await page.locator("#detail").innerText(),actions=await page.locator("#detail button:visible").allInnerTexts();
   assert(details.includes(status),role+"/"+slug+": wrong state");
   assert(details.includes("Come procedere"),role+"/"+slug+": no next step");
   assert(details.includes("Residuo"),role+"/"+slug+": missing balance");
   if(slug==="paid")assert(!actions.includes("Registra pagamento"),"paid invoice offers payment");
   if(role==="t")assert.equal(actions.length,0,"accountant has write action");
   if(role!=="t"&&slug==="draft")assert(actions.includes("Approva e contabilizza"),"draft has no authorized action");
   if(role==="m")await page.screenshot({path:"/qa-results/finance-"+slug+".png"});
   results[role].invoices.push({slug,status,actions});
  }
  await page.goto(base+"/app/sales-invoice/ACC-SINV-2026-00004");
  await page.locator(".cc-finance-context").waitFor({state:"visible",timeout:30000});
  const form=await page.locator(".cc-finance-context").innerText();
  assert(form.includes("Fattura paziente")&&form.includes("Come procedere"),"native invoice context absent");
  if(role==="m"){
   assert.equal(await page.getByRole("button",{name:"Get Items From"}).filter({visible:true}).count(),0,"upstream button visible");
   assert.equal(await page.locator('.form-tabs-list .nav-item:visible').count(),2,"technical tabs visible");
   await page.screenshot({path:"/qa-results/native-invoice-simple.png"});
   await page.getByRole("button",{name:"Dettagli contabili"}).click();
   assert(await page.locator('.form-tabs-list .nav-item:visible').count()>2,"advanced details inaccessible");
   assert(await page.locator('button:visible').filter({hasText:"Get Items From"}).count()>0,"native technical action inaccessible");
   await page.screenshot({path:"/qa-results/native-invoice-advanced.png"});
  }
  if(role==="f")assert(await page.locator('.form-tabs-list .nav-item:visible').count()>2,"Finance details hidden");
  results[role].native_invoice=true;
  await page.goto(base+"/app/purchase-invoice/ACC-PINV-2026-00001");
  await page.locator(".cc-finance-context").waitFor({state:"visible",timeout:30000});
  results[role].professional_invoice=(await page.locator(".cc-finance-context").innerText()).includes("Fattura professionista");
  assert(results[role].professional_invoice);
  await context.close();
 }
 const context=await browser.newContext({viewport:{width:1440,height:900},locale:"it-IT",serviceWorkers:"block"}),page=await context.newPage(),errors=[];
 page.on("pageerror",e=>errors.push(e.message));await login(page,"f");
 for(const [route,needle,file] of [
  ["/app/payment-entry","Incasso","native-payment.png"],
  ["/app/bank-transaction","Movimento bancario","native-bank.png"]
 ]){
  await page.goto(base+route);await page.locator(".list-row .list-subject a").first().click();
  await page.locator(".cc-finance-context").waitFor({state:"visible",timeout:30000});
  const text=await page.locator(".cc-finance-context").innerText();
  assert(text.includes(needle)&&text.includes("Come procedere"),route+": context absent");
  await page.screenshot({path:"/qa-results/"+file});
 }
 for(const [view,label] of [["Banca","Movimenti e riconciliazioni"],["SdI","Simulazione SdI"],["TS","Simulazione TS"]]){
  await page.goto(base+"/app/cc-unified-desk?cc_view=finance&cc_fin_view="+encodeURIComponent(view));
  await page.locator("#center").waitFor({timeout:30000});await page.locator("#center").selectOption(center);
  await page.locator(".cc-finance-guide").waitFor({state:"visible",timeout:30000});
  assert((await page.locator(".cc-finance-guide").innerText()).includes(label),view+": guidance absent");
  if(view==="Banca"){await page.locator("#finance-content tr[data-name]").first().click();await page.waitForFunction(()=>document.querySelector("#detail")?.innerText?.includes("Da riconciliare"));}
  if(view==="Banca")assert((await page.locator("#detail").innerText()).includes("Da riconciliare"),"bank detail lacks balance");
  await page.screenshot({path:"/qa-results/finance-"+view.toLowerCase()+".png"});
 }
 assert.deepEqual(errors,[],"Finance JavaScript errors");
 results.other={payment_bank_fiscal:"PASS",errors,cancelled_invoice:"No cancelled synthetic invoice exists; read-only boundary only"};
 fs.writeFileSync("/qa-results/finance.json",JSON.stringify(results,null,2));
 console.log("PASS premium UX finance",JSON.stringify(results));
 await context.close();await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
