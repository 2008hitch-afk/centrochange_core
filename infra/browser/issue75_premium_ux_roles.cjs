// Seven synthetic roles, landing, menu boundaries and responsive shell.
const {chromium}=require("playwright"),assert=require("node:assert/strict"),fs=require("node:fs");
const users=JSON.parse(fs.readFileSync("/qa-fixture.json")).fixture.users;
const base="http://centrochange.local:8080",results={};
const expected={
 m:{home:"agenda",agenda:true,finance:true,bank:true},
 s:{home:"agenda",agenda:true,finance:true,bank:true},
 a:{home:"agenda",agenda:true,finance:false,bank:false},
 b:{home:"agenda",agenda:true,finance:false,bank:false},
 c:{home:"agenda",agenda:true,finance:false,bank:false},
 f:{home:"finance",agenda:false,finance:true,bank:true},
 t:{home:"finance",agenda:false,finance:true,bank:false}
};
(async()=>{
 const browser=await chromium.launch({args:["--host-resolver-rules=MAP centrochange.local 127.0.0.1","--no-proxy-server","--disable-dev-shm-usage"]});
 for(const [role,want] of Object.entries(expected)){
  const context=await browser.newContext({viewport:{width:1440,height:900},locale:"it-IT",serviceWorkers:"block"});
  const page=await context.newPage(),errors=[];page.on("pageerror",e=>errors.push(e.message));
  await page.goto(base+"/login");await page.locator("#login_email").fill(users[role].name);
  await page.locator("#login_password").fill(users[role].password);await page.locator(".form-login button[type=submit]").click();
  await page.locator("#cc-desk-sidebar").waitFor({timeout:45000});
  assert(page.url().includes("cc_view="+want.home),role+": incorrect login landing");
  await page.locator(".cc-desk-surface").waitFor({timeout:45000});
  for(const [path,expectedView] of [["/desk",want.home],["/app",want.home],["/",want.home]]){
   await page.goto(base+path);await page.locator("#cc-desk-sidebar").waitFor({timeout:45000});
   assert(page.url().includes("cc_view="+expectedView),role+": "+path+" launcher leak");
  }
  const titles=await page.locator("#cc-desk-sidebar a[title]").evaluateAll(links=>links.map(a=>a.title));
  assert.equal(titles.includes("Agenda"),want.agenda,role+": Agenda menu");
  assert.equal(titles.includes("Finanza"),want.finance,role+": Finanza menu");
  assert.equal(titles.includes("Banca"),want.bank,role+": Banca menu");
  results[role]={landing:want.home,menu:titles,sizes:[],errors};
  for(const [size,width,height] of [["desktop",1440,900],["tablet",820,1180],["mobile",390,844]]){
   await page.setViewportSize({width,height});await page.waitForTimeout(250);
   if(width<992){
    const toggle=page.locator(".cc-mobile-toggle");await toggle.click();await page.waitForTimeout(250);
    assert(await page.locator("#cc-desk-sidebar").evaluate(el=>el.getBoundingClientRect().left>=-1),role+"/"+size+": sidebar cut");
    await toggle.click();
   }
   const layout=await page.evaluate(()=>({overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),
    shell:document.querySelectorAll("#cc-desk-sidebar").length,upstream:[...document.querySelectorAll("img")].filter(el=>{const r=el.getBoundingClientRect();return r.width&&r.height&&/erpnext|frappe|marley/i.test(el.src)}).length}));
   assert(layout.overflow<=2&&layout.shell===1&&layout.upstream===0,role+"/"+size+": "+JSON.stringify(layout));
   await page.screenshot({path:"/qa-results/role-"+role+"-"+size+".png"});
   results[role].sizes.push({size,...layout});
  }
  assert.deepEqual(errors,[],role+": JavaScript error");
  await context.close();
 }
 fs.writeFileSync("/qa-results/roles.json",JSON.stringify(results,null,2));
 console.log("PASS premium UX roles and responsive",Object.keys(results).join(","));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
