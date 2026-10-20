const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '../..');
const js = path.join(root, 'app/centrochange_core/centrochange_core/public/js/rome_date.js');
const csv = path.join(root, 'app/centrochange_core/centrochange_core/translations/it.csv');
const source = fs.readFileSync(js, 'utf8');
const translation = fs.readFileSync(csv, 'utf8');
const expected = [
  ['Occupation','Professione'],['Marital Status','Stato civile'],
  ['Appointments and Encounters','Sedute e visite'],
  ['Billing and Payments','Fatturazione e pagamenti'],
  ['Annual Billing','Fatturato annuale'],
  ['Free Followup Details','Visite di controllo gratuite'],
  ['Address and Contacts','Indirizzi e contatti'],
  ['Immutable Incoming Source','Origine del documento ricevuto (non modificabile)'],
  ['Total Taxes and Charges','Totale imposte e oneri']
];
for (const [source,target] of expected) {
  assert(translation.includes(`${source},${target}`), `${source} missing`);
}
assert(!/Get Items From,/.test(translation) || translation.includes('Get Items From,Importa voci da'));

(async()=>{
  const locale = await import('data:text/javascript,'+encodeURIComponent(source));
  assert.equal(locale.italianDate('2026-12-31'),'31/12/2026');
  assert.equal(locale.italianDateTime('2026-12-31 23:59:00'),'31/12/2026 23:59');
  assert.equal(locale.italianDateTime('2026-03-29T00:30:00Z'),'29/03/2026 01:30');
  assert.equal(locale.italianDateTime('2026-03-29T01:30:00Z'),'29/03/2026 03:30');
  assert.equal(locale.italianDateTime('2026-10-25T01:30:00Z'),'25/10/2026 02:30');
  assert.equal(locale.italianTime('09:05:00'),'09:05');
  assert.equal(locale.romeToday(new Date('2026-12-31T23:30:00Z')),'2027-01-01');
  for (const value of ['2026-01-31','2026-02-28','2026-12-31'])
    assert(/^\d{2}\/\d{2}\/\d{4}$/.test(locale.italianDate(value)));
  assert(!source.includes('toLocaleDateString(\'en-CA\''));
  console.log('PASS issue134 locale CSV, Europe/Rome boundaries and 24h');
})().catch(error=>{console.error(error);process.exitCode=1});
