const {chromium}=require('playwright'),fs=require('node:fs'),path=require('node:path');
const base=process.env.CC_BASE_URL,f=JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE,'utf8'));
const out=process.env.CC_ISSUE137_OUTPUT,checks=[];
(async()=>{const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});let invoice,privateFile;
try{for(const role of ['f','t','a']){const ctx=await browser.newContext(),p=await ctx.newPage();try{
await p.goto(base+'/login');await p.locator('#login_email').fill(f.users[role].name);await p.locator('#login_password').fill(f.users[role].password);await p.getByRole('button',{name:'Continua',exact:true}).click();await p.waitForURL(u=>/^\/(app|desk)/.test(new URL(u).pathname));
if(role==='f'){const list=await p.evaluate(async()=>{const r=await fetch('/api/resource/Sales%20Invoice?fields=%5B%22name%22%5D&limit_page_length=10');return {status:r.status,data:await r.json()}});invoice=list.data.data?.[0]?.name;checks.push({role,kind:'find_existing_invoice',status:list.status,found:!!invoice});}
if(invoice){const result=await p.evaluate(async invoice=>{const url='/api/method/centrochange_core.finance.attachments.list_for_document?doctype=Sales%20Invoice&name='+encodeURIComponent(invoice);const r=await fetch(url);const j=await r.json();return {status:r.status,count:j.message?.length??null,errorType:typeof j.exc_type==='string'?j.exc_type:null,fileUrl:j.message?.[0]?.file_url??null};},invoice);if(role==='f')privateFile=result.fileUrl;checks.push({role,kind:'private_attachment_list',status:result.status,count:result.count,errorType:result.errorType});}
if(privateFile){const download=await p.evaluate(async url=>{const r=await fetch(url);return {status:r.status,bytes:(await r.arrayBuffer()).byteLength};},privateFile);checks.push({role,kind:'private_attachment_download',...download});}
}finally{await ctx.close();}}}finally{await browser.close();}
fs.writeFileSync(path.join(out,'attachment-readonly.json'),JSON.stringify({checks},null,2));console.log(JSON.stringify({checks}));})().catch(e=>{console.error(e.stack);process.exit(2)});
