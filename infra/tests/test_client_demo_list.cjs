const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const source = fs.readFileSync(path.resolve(__dirname,'../../app/centrochange_core/centrochange_core/public/js/cc_catalog_finance_list.js'),'utf8');
function settings(user,roles) {
  const frappe={session:{user},user_roles:roles,listview_settings:{},utils:{escape_html(value){
    return value.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
  }}};
  vm.runInNewContext(source,{frappe});
  return frappe.listview_settings;
}
const client=settings('demo',['CC Manager']);
const sales=client['Sales Invoice'];
assert(sales,'client invoice List View customization missing');
assert.equal(sales.formatters.customer('CC-MVP-POS-20261019-001'),'Paziente dimostrativo POS');
assert.equal(sales.formatters.customer_name('Beta'),'Beta');
assert.equal(sales.formatters.customer('<script>'),'&lt;script&gt;');
assert.equal(sales.hide_name_column,undefined,'canonical document number must remain available');
assert.equal(settings('Administrator',['System Manager'])['Sales Invoice'],undefined,
  'technical Administrator must retain native view');
console.log('client demo native invoice subject: PASS');
