// Chromium acceptance of issue #75: one session, real navigation and video.
const {chromium}=require("playwright");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const users=JSON.parse(fs.readFileSync("/qa-fixture.json")).fixture.users;
const base="http://centrochange.local:8080";
const steps=[
  ["agenda","Agenda","cc-unified-desk"],
  ["ricerca-pazienti","Ricerca pazienti","cc-unified-desk"],
  ["pazienti","Anagrafica pazienti","patient"],
  ["professionisti","Anagrafica professionisti","healthcare-practitioner"],
  ["fatture","Fatture pazienti","sales-invoice"],
  ["incassi","Incassi e pagamenti","payment-entry"],
  ["movimenti","Movimenti bancari","bank-transaction"],
  ["banca","Banca","cc-unified-desk"],
  ["report","Report professionisti","cc-unified-desk"],
  ["agenda-ritorno","Agenda","cc-unified-desk"]
];
function visible(el){if(!el)return false;const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=="none"&&s.visibility!=="hidden";}
(async()=>{
 const browser=await chromium.launch({headless:true,args:["--host-resolver-rules=MAP centrochange.local 127.0.0.1","--no-proxy-server","--disable-dev-shm-usage"]});
 const context=await browser.newContext({viewport:{width:1440,height:900},locale:"it-IT",serviceWorkers:"block",recordVideo:{dir:"/qa-results",size:{width:1440,height:900}}});
 const page=await context.newPage(),errors=[],results=[];let documents=0;
 page.on("pageerror",e=>errors.push(e.message));
 page.on("request",r=>{if(r.isNavigationRequest()&&r.resourceType()==="document"){documents++;console.log("DOC",r.url());}});
 await page.addInitScript(()=>{
  window.__ccSamples=[];
  const visible=el=>{if(!el)return false;const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=="none"&&s.visibility!=="hidden"};
  setInterval(()=>{
   const upstream=[...document.querySelectorAll("img")].filter(visible).some(img=>/erpnext|frappe|marley/i.test([img.src,img.alt].join(" ")));
   const splash=visible(document.querySelector(".splash"));
   const shell=visible(document.querySelector("#cc-desk-sidebar"));
   const content=visible(document.querySelector(".cc-desk-surface"))||visible(document.querySelector(".list-row-head"))||visible(document.querySelector(".form-layout"));
   window.__ccSamples.push({at:performance.now(),splash,upstream,shell,content,url:location.pathname+location.search});
  },50);
 });
 await page.goto(base+"/login");await page.locator("#login_email").fill(users.m.name);await page.locator("#login_password").fill(users.m.password);
 await page.locator(".form-login button[type=submit]").click();
 await page.locator("#cc-desk-sidebar").waitFor({timeout:60000});
 await page.locator(".cc-desk-surface").waitFor({timeout:60000});
 assert(page.url().includes("cc_view=agenda"),"login must land on Agenda");
 await page.evaluate(()=>{window.__ccSidebar=document.querySelector("#cc-desk-sidebar");window.__ccSamples=[];});
 const docsAtLogin=documents;
 for(const [slug,label,path] of steps){
  const link=page.locator('#cc-desk-sidebar a[title="'+label+'"]').first();
  const group=link.locator("xpath=ancestor::details").first();
  if(await group.count() && !(await group.evaluate(el=>el.open))) await group.locator("summary").click();
  const start=Date.now(),before=documents;
  await link.click();
  await page.waitForURL(url=>url.pathname.includes(path),{timeout:30000});
  if(path==="cc-unified-desk")await page.locator(".cc-desk-surface").waitFor({timeout:30000});
  else await page.locator(".list-row-head:visible").first().waitFor({timeout:30000});
  await page.waitForTimeout(250);
  const sample=await page.evaluate(()=>({
   persistentSidebar:document.querySelector("#cc-desk-sidebar")===window.__ccSidebar,
   samples:window.__ccSamples.splice(0),
   overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),
   title:document.querySelector("#page-title")?.textContent||document.querySelector(".page-head")?.innerText?.slice(0,60)
  }));
  const splashCount=sample.samples.filter(s=>s.splash).length,upstreamCount=sample.samples.filter(s=>s.upstream).length;
  console.log("STEP",slug,"docs",documents-before,"url",page.url());
  assert.equal(documents,before,slug+": unexpected document reload");
  assert.equal(splashCount,0,slug+": splash during internal navigation");
  assert.equal(upstreamCount,0,slug+": upstream branding visible");
  assert(sample.persistentSidebar,slug+": sidebar replaced");
  assert(sample.overflow<=2,slug+": horizontal overflow");
  await page.screenshot({path:"/qa-results/"+slug+".png"});
  results.push({slug,url:page.url(),route_ms:Date.now()-start,document_requests:documents-before,
   content_unavailable_samples:sample.samples.filter(s=>!s.content).length,splash_samples:splashCount,
   persistent_sidebar:sample.persistentSidebar,overflow_px:sample.overflow,title:sample.title});
 }
 assert.equal(documents,docsAtLogin,"full document reload during journey");
 assert.deepEqual(errors,[],"JavaScript errors");
 fs.writeFileSync("/qa-results/journey.json",JSON.stringify({documents_at_login:docsAtLogin,results,errors},null,2));
 console.log("PASS issue75 premium UX journey",JSON.stringify(results.map(r=>({step:r.slug,ms:r.route_ms,unavailable:r.content_unavailable_samples}))));
 const video=page.video();
 await context.close();
 if(video)fs.renameSync(await video.path(),"/qa-results/journey.webm");
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
