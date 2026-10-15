const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

(async()=>{
  const source=fs.readFileSync(path.resolve(__dirname,
    '../../app/centrochange_core/centrochange_core/public/js/accounting_labels.js'),'utf8');
  const {fiscalOutcome}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
  assert.equal(fiscalOutcome({status:'ACCEPTED',attempt_count:1}),
    'Esito acquisito nella simulazione');
  assert.equal(fiscalOutcome({status:'ELIGIBILITY_PENDING',attempt_count:0}),
    'Nessun tentativo simulato');
  assert.equal(fiscalOutcome({status:'FAILED_RETRYABLE',attempt_count:1,error_class:'TEMP'},
    value=>value==='TEMP'?'Errore temporaneo':'Errore sconosciuto'),'Errore temporaneo');
  assert.equal(fiscalOutcome({status:'SUBMITTED',attempt_count:1}),
    'Consulta lo stato del tentativo');
  console.log('issue139 fiscal outcome: 4 states PASS');
})().catch(error=>{console.error(error);process.exitCode=1});
