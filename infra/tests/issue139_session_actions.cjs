const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

async function main() {
  const source=fs.readFileSync(path.resolve(__dirname,'../../app/centrochange_core/centrochange_core/public/js/session_actions.js'),'utf8');
  const {sessionActions}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
  const base={appointment_date:'2026-10-14',appointment_time:'09:00:00',duration:60,
              cc_closure_state:'Pending',status:'Open',cc_performed:0,cc_economic_state:'Non Due'};
  const manager=['CC Manager'],professional=['CC Professional'];
  assert.deepEqual(sessionActions(base,professional,'2026-10-14T08:00:00'),
                   {close:false,move:true,cancel:true,reopen:false,waive:false});
  assert.equal(sessionActions(base,professional,'2026-10-14T10:00:00').close,true);
  assert.equal(sessionActions(base,professional,'2026-10-15T08:00:00').move,false);
  const cancelled={...base,status:'Cancelled',cc_closure_state:'Closed',cc_economic_state:'Due'};
  assert.deepEqual(sessionActions(cancelled,manager,'2026-10-14T12:00:00'),
                   {close:false,move:false,cancel:false,reopen:true,waive:true});
  assert.equal(sessionActions(cancelled,professional,'2026-10-14T12:00:00').waive,false);
  const reopened={...base,cc_closure_state:'Reopened'};
  assert.equal(sessionActions(reopened,manager,'2026-10-20T11:00:00').move,false);
  assert.equal(sessionActions({...base,cc_performed:1},manager,'2026-10-14T10:00:00').cancel,false);
  console.log('issue139 session action presentation: 7 cases PASS');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
