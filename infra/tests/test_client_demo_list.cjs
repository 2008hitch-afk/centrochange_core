const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const source = fs.readFileSync(path.resolve(__dirname,'../../app/centrochange_core/centrochange_core/public/js/cc_catalog_finance_list.js'),'utf8');
function settings(user,roles) {
  class Observer { constructor(callback){this.callback=callback} observe(element){element.observer=this} }
  const frappe={session:{user},user_roles:roles,listview_settings:{},utils:{escape_html(value){
    return value.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
  }}};
  vm.runInNewContext(source,{frappe,MutationObserver:Observer,__:(value)=>({Practitioner:'Professionista',
    'Allow Booking For':'Prenotabile per'})[value]||value});
  return frappe.listview_settings;
}
const client=settings('demo',['CC Manager']);
const sales=client['Sales Invoice'];
assert(sales,'client invoice List View customization missing');
assert.equal(sales.formatters.customer('CC-MVP-POS-20261019-001'),'Paziente dimostrativo POS');
assert.equal(sales.formatters.customer_name('Beta'),'Beta');
assert.equal(sales.formatters.customer('<script>'),'&lt;script&gt;');
assert.equal(sales.hide_name_column,undefined,'canonical document number must remain available');
assert.match(sales.formatters.posting_date('2026-10-05'),
  /title="Data contabile: 05\/10\/2026"/);
assert.match(sales.formatters.posting_date('2026-10-05'),
  /data-filter="posting_date,=,2026-10-05"/,
  'native filter must retain the canonical ISO date');
assert.match(client['Purchase Invoice'].formatters.due_date('2026-10-31'),
  /31\/10\/2026/);
assert.equal(client['Payment Entry'].formatters.posting_date('<script>'),'&lt;script&gt;');
const nativeColumn={label:'Customer Name',fieldname:'customer_name'};
sales.onload({columns:[{df:nativeColumn}],page:{set_title(){}}});
assert.equal(nativeColumn.label,'Paziente');
assert.equal(nativeColumn.fieldname,'customer_name','canonical sort field must remain unchanged');
const appointment=client['Appointment Type'].formatters.allow_booking_for('Practitioner');
assert.match(appointment,/title="Prenotabile per: Professionista"/);
assert.match(appointment,/data-filter="allow_booking_for,=,Practitioner"/,
  'translated label must preserve the canonical native filter');
const filterButton={title:'1 Filter Applied',getAttribute(){return this.title},
  setAttribute(name,value){this.title=value;this.observer?.callback()}};
client.Item.onload({columns:[],filter_area:{filter_button:{0:filterButton}},page:{set_title(){}}});
assert.equal(filterButton.title,'1 filtro applicato');
filterButton.setAttribute('title','2 Filters Applied');
assert.equal(filterButton.title,'2 filtri applicati');
assert.equal(settings('Administrator',['System Manager'])['Sales Invoice'],undefined,
  'technical Administrator must retain native view');
console.log('client demo native invoice subject: PASS');
