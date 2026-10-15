// Check the actual Agenda input helper in both browser locales without touching DEV data.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {chromium} = require('playwright');

const source = fs.readFileSync(path.resolve(__dirname,
  '../../app/centrochange_core/centrochange_core/public/js/workspace.js'), 'utf8');
const helper = source.match(/function input\(name,type='text',value='',required=true\)\{[\s\S]*?\n\}/)?.[0];
if (!helper) throw Error('Agenda input helper not found');
const context = {esc: value => String(value).replaceAll('&', '&amp;').replaceAll('"', '&quot;')};
vm.createContext(context);
vm.runInContext(helper, context);

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox']});
  try {
    for (const locale of ['en-US', 'it-IT']) {
      const session = await browser.newContext({locale});
      const page = await session.newPage();
      await page.setContent('<form>' + context.input('time', 'time', '09:00') + '</form>');
      const result = await page.locator('[name=time]').evaluate(input => {
        const initial = {type: input.type, placeholder: input.placeholder,
          value: input.value, valid: input.checkValidity()};
        input.value = '09:00 AM';
        const amValid = input.checkValidity();
        input.value = '23:59';
        const lateValid = input.checkValidity();
        input.value = '24:00';
        const beyondValid = input.checkValidity();
        return {...initial, amValid, lateValid, beyondValid};
      });
      if (result.type !== 'text' || result.placeholder !== 'HH:mm' || result.value !== '09:00' ||
          !result.valid || result.amValid || !result.lateValid || result.beyondValid)
        throw Error(`Invalid 24-hour control in ${locale}: ${JSON.stringify(result)}`);
      console.log(`${locale}: 24-hour input PASS`);
      await session.close();
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
