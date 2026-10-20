const test = require('node:test');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const {collectVisibleText} = require('../browser/issue134_visible_text_inventory.cjs');

test('inventory collects rendered text, accessible labels and options, excluding hidden content', async () => {
  const browser = await chromium.launch({headless:true,args:['--no-sandbox']});
  try {
    const page = await browser.newPage();
    await page.setContent(`<main><h1>Fattura</h1><label for="d">Data</label>
      <input id="d" placeholder="GG/MM/AAAA" title="Scegli data" />
      <button aria-label="Salva documento">Salva</button>
      <select><option>Bozza</option><option>Submitted</option></select>
      <div style="display:none">Technical Hidden</div>
      <div aria-hidden="true">Hidden For User</div></main>`);
    const lines = await collectVisibleText(page);
    const values = lines.map(x => x.text);
    for (const expected of ['Fattura','Data','GG/MM/AAAA','Scegli data','Salva documento',
      'Salva','Bozza','Submitted']) assert(values.includes(expected), expected);
    assert(!values.includes('Technical Hidden'));
    assert(!values.includes('Hidden For User'));
  } finally { await browser.close(); }
});
