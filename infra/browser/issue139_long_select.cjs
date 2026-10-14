// Browser contract for native short selects and searchable long selects; no DEV calls.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');

const source=fs.readFileSync(path.resolve(__dirname,
  '../../app/centrochange_core/centrochange_core/public/js/search_select.js'),'utf8')
  .replace("import {clean,person} from './report_ui.js';",
    'const clean=value=>String(value||""); const person=clean;');
if(!source.includes('export function enhanceSelectors'))throw Error('Search component source changed');
const script=source.replace(/export (const|function) /g,'$1 ')+'\nwindow.enhanceSelectors=enhanceSelectors;';

(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});try{
  for(const width of [390,1440]){
    const context=await browser.newContext({viewport:{width,height:844},locale:'it-IT'});
    const page=await context.newPage();
    await page.setContent('<form><label>Metodo<select name="method"><option value="">Seleziona</option>'+[1,2,3].map(n=>`<option value="m${n}">Metodo ${n}</option>`).join('')+'</select></label><label>Documento<select name="invoice" required><option value="">Seleziona</option>'+Array.from({length:12},(_,n)=>`<option value="i${n}">Documento ${n}</option>`).join('')+'</select></label></form>');
    await page.addScriptTag({type:'module',content:script});
    await page.waitForFunction(()=>typeof window.enhanceSelectors==='function');
    await page.evaluate(()=>window.enhanceSelectors(document));
    assert.equal(await page.locator('select[name=method]').evaluate(el=>el.hidden),false);
    assert.equal(await page.locator('select[name=invoice]').evaluate(el=>el.hidden),true);
    const input=page.getByRole('combobox',{name:'Cerca documento'});
    await input.fill('Documento 11');
    await page.getByRole('option',{name:'Documento 11'}).waitFor();
    await input.press('ArrowDown');await input.press('Enter');
    assert.equal(await page.locator('select[name=invoice]').inputValue(),'i11');
    await input.fill('nessuna corrispondenza');
    await page.getByRole('status').getByText('Nessun risultato autorizzato.').waitFor();
    assert.equal(await page.locator('select[name=invoice]').inputValue(),'');
    console.log(`${width}: short native, long keyboard/empty PASS`);
    await context.close();
  }
}finally{await browser.close()}})().catch(error=>{console.error(error);process.exitCode=1});
