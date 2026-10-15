const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

async function main(){
  const source=fs.readFileSync(path.resolve(__dirname,'../../app/centrochange_core/centrochange_core/public/js/rome_date.js'),'utf8');
  const {romeToday}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
  const cases=[
    ['2026-10-14T22:30:00Z','2026-10-15'],
    ['2026-03-29T00:30:00Z','2026-03-29'],
    ['2026-03-29T22:30:00Z','2026-03-30'],
    ['2026-10-25T00:30:00Z','2026-10-25'],
    ['2026-10-25T23:30:00Z','2026-10-26'],
  ];
  for(const [instant,expected] of cases)assert.equal(romeToday(new Date(instant)),expected,instant);
  console.log('issue139 Rome date: 5 midnight/DST cases PASS');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
