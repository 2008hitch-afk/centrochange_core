const {chromium}=require('playwright');
const {execFileSync}=require('child_process');
const fs=require('fs');const path=require('path');const assert=require('assert');
const out=process.env.CC_ARTIFACT_DIR;fs.mkdirSync(out,{recursive:true});
function frappe(code){return execFileSync('docker',['exec','-e','FRAPPE_STREAM_LOGGING=1','-w','/home/frappe/frappe-bench','cc183-clone-backend','env/bin/python','-c',code],{encoding:'utf8'}).trim()}
const discover=`import frappe,json
frappe.init('centrochange.local',sites_path='sites');frappe.connect()
c=frappe.get_all('Branch',filters={'cc_operational':1},pluck='name',order_by='name',limit_page_length=1)[0]
u=frappe.get_all('CC Center Membership',filters={'center':c,'active':1},pluck='user',limit_page_length=0)
def who(role):return frappe.get_all('Has Role',filters={'role':role,'parent':['in',u]},pluck='parent',limit_page_length=1)[0]
m=who('CC Manager');ps=frappe.get_all('Has Role',filters={'role':'CC Professional','parent':['in',u]},pluck='parent',limit_page_length=0);rec=frappe.get_all('Healthcare Practitioner',filters={'user_id':['in',ps],'status':'Active'},fields=['name','user_id'],limit_page_length=1)[0];p=rec.user_id;pr=rec.name
print(json.dumps({'center':c,'manager':m,'professional':p,'practitioner':pr}))`;
const env=JSON.parse(frappe(discover));
function sid(user){return frappe(`import frappe\nfrom werkzeug.test import EnvironBuilder\nfrom frappe.sessions import Session\nfrappe.init('centrochange.local',sites_path='sites');frappe.connect();frappe.request=EnvironBuilder().get_request()\nSession(user=${JSON.stringify(user)}).start();print(frappe.session.sid)`)}
const managerSid=sid(env.manager),proSid=sid(env.professional);
(async()=>{const b=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server']});try{
 for(const [width,tag] of [[1440,'desktop'],[390,'mobile']]){
  const ctx=await b.newContext({viewport:{width,height:900},locale:'it-IT',timezoneId:'Europe/Rome'});await ctx.addCookies([{name:'sid',value:managerSid,domain:'centrochange.local',path:'/'}]);const p=await ctx.newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.goto('http://centrochange.local:8099/premium#Gestione%20accessi',{waitUntil:'networkidle'});await p.getByRole('heading',{name:'Gestione accessi'}).waitFor();await p.locator('.panel tbody tr').first().waitFor();
  await p.screenshot({path:path.join(out,`access-${tag}.png`)});
  for(const value of ['0','1']){
   await p.getByRole('button',{name:'Appartenenza',exact:true}).click();const dialog=p.getByRole('dialog',{name:'Appartenenza al centro'});
   await dialog.getByLabel('Utente').selectOption(env.professional);await dialog.getByLabel('Nuovo stato').selectOption(value);await dialog.getByLabel('Motivo della modifica').fill('AUDIT10 prova sintetica');await dialog.getByRole('button',{name:'Rivedi modifica'}).click();
   assert((await dialog.innerText()).includes('AUDIT10 prova sintetica'));const response=p.waitForResponse(r=>r.url().includes('security.lifecycle.set_membership')&&r.request().method()==='POST');await dialog.getByRole('button',{name:'Conferma modifica'}).click();assert((await response).ok());await dialog.waitFor({state:'hidden'});
  }
  await p.goto('http://centrochange.local:8099/premium#Registro%20modifiche',{waitUntil:'networkidle'});await p.getByRole('heading',{name:'Registro modifiche'}).waitFor();const event=p.getByRole('row',{name:/AUDIT10 prova sintetica/}).first();await event.waitFor({timeout:15000});await event.click();const detail=p.getByRole('dialog',{name:'Appartenenza al centro'});await detail.waitFor();assert((await detail.innerText()).includes('AUDIT10 prova sintetica'));await p.screenshot({path:path.join(out,`audit-${tag}.png`)});assert.deepStrictEqual(errors,[]);await ctx.close();console.log('AUDIT10_BROWSER_MANAGER_PASS',tag)
 }
 const ctx=await b.newContext();await ctx.addCookies([{name:'sid',value:proSid,domain:'centrochange.local',path:'/'}]);const p=await ctx.newPage();await p.goto('http://centrochange.local:8099/premium#Agenda',{waitUntil:'networkidle'});assert.strictEqual(await p.getByRole('button',{name:'Gestione accessi',exact:true}).count(),0);assert.strictEqual(await p.getByRole('button',{name:'Registro modifiche',exact:true}).count(),0);
 const statuses=await p.evaluate(async center=>{const token=document.querySelector('meta[name="csrf-token"]').content;const get=async url=>(await fetch(url)).status;const post=async (url,data)=>(await fetch(url,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded','X-Frappe-CSRF-Token':token},body:new URLSearchParams(data)})).status;return [await get('/api/method/centrochange_core.operations.workspace.management_context?center='+encodeURIComponent(center)),await get('/api/method/centrochange_core.security.audit_view.events?start=2000-01-01&end=2000-12-31'),await post('/api/method/centrochange_core.security.lifecycle.set_membership',{user:'nobody@example.invalid',center,active:'0',reason:'negative'})]},env.center);assert(statuses.every(x=>[401,403,417].includes(x)),JSON.stringify(statuses));console.log('AUDIT10_BROWSER_PROFESSIONAL_API_DENIAL_PASS',statuses.join(','));await ctx.close();
 }finally{await b.close()}})().catch(e=>{console.error(e);process.exit(1)});
