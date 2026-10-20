const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '../..');
const js = name => path.join(root, 'app/centrochange_core/centrochange_core/public/js', name);

function form(file, doctype, roles, doc = {}) {
  const handlers = {};
  const labels = {};
  const descriptions = {};
  const options = {};
  const heatmap = {text:null, html:null};
  const collapsed = [];
  const inserted = [];
  const removed = [];
  const buttons = {};
  const fields = new Proxy({}, {get: (_, key) => ({df: {reqd: key === 'patient_name'}, grid: undefined})});
  const main = {find(selector) {
    return {remove() {removed.push(selector); return this;}, first() {return this;},
      before(html) {inserted.push(html); return this;}};
  }};
  const frm = {doc, doctype, fields_dict: fields,
    dashboard: {data: {heatmap:true,heatmap_message:'Original English'},
      heatmap_area:{body:{find(){return {text(value){heatmap.text=value;},html(value){heatmap.html=value;}};}}}},
    layout: {tabs: [], refresh_tabs() {}, sections: ['more_info','allergy_medical_and_surgical_history','risk_factors',
      'charges','free_followup_details_section','account_details'].map(fieldname =>
      ({df: {fieldname}, collapse(value) {collapsed.push([fieldname,value]);}}))},
    page: {main, set_title() {}, get_inner_group_button() {return {toggle() {}};}},
    is_new() {return !doc.name;}, set_df_property(field, property, value) {
      if (property === 'label') labels[field] = value;
      if (property === 'description') descriptions[field] = value;
      if (property === 'options') options[field] = value;
      assert.notEqual(property, 'reqd', 'Client script must preserve required fields');
      assert.notEqual(property, 'read_only', 'Client script must preserve field permissions');
    }, toggle_display() {}, add_custom_button(label, fn) {buttons[label] = fn;},
    remove_custom_button(label) {delete buttons[label];}, trigger(event) {handlers[doctype].refresh(frm);}};
  const context = {window: {}, document: {body: {dataset: {}}},
    frappe: {session: {user: roles.includes('Administrator') ? 'Administrator' : 'demo'}, user_roles: roles,
      utils:{escape_html:value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))},
      ui: {form: {on(name, events) {handlers[name] = events;}}}},
    __: value => ({
      'This is based on transactions against this Patient. See timeline below for details':
        'Calcolo basato sulle operazioni del paziente. Consulta la cronologia per i dettagli.',
      'This is based on stock movement. See {0} for details':
        'Calcolo basato sui movimenti di magazzino. Consulta {0} per i dettagli',
      'Stock Ledger':'Movimenti di magazzino'
    })[value] || value, Intl, Date, Number, String, Object, Set, Boolean};
  vm.runInNewContext(fs.readFileSync(js(file), 'utf8'), context, {filename: file});
  assert.ok(handlers[doctype], `${doctype} handler registered`);
  handlers[doctype].refresh(frm);
  return {frm, labels, descriptions, options, heatmap, inserted, removed, buttons, collapsed,
    dataset:context.document.body.dataset};
}

const patient = form('cc_patient_form.js', 'Patient', ['CC Manager'],
  {name: 'PAT-1', patient_name: 'Mario Rossi', status: 'Active'});
assert.equal(patient.labels.patient_name, 'Nome e cognome');
assert.match(patient.inserted.join(''), /Come compilare/);
assert.match(patient.inserted.join(''), /Salva/);
assert.equal(patient.labels.medical_history_tab, 'Dati clinici riservati');
assert.ok(patient.collapsed.some(([name,value]) => name === 'more_info' && value === true));
assert.equal(patient.dataset.ccNativeTools, '0');
assert.match(patient.heatmap.text, /Calcolo basato sulle operazioni/);
assert.equal(typeof patient.buttons['Strumenti e tracciabilità'], 'function');
patient.buttons['Strumenti e tracciabilità']();
assert.equal(patient.dataset.ccNativeTools, '1');
assert.equal(form('cc_patient_form.js', 'Patient', ['Administrator'], {}).inserted.length, 0);

const practitioner = form('cc_practitioner_form.js', 'Healthcare Practitioner', ['CC Manager'],
  {name: 'HPR-1', practitioner_name: 'Alfa', status: 'Active'});
assert.equal(practitioner.labels.charges, 'Tariffe professionali');
assert.equal(practitioner.labels.free_followup_details_section, 'Visite di controllo gratuite');
assert.ok(practitioner.collapsed.some(([name,value]) => name === 'charges' && value === true));
assert.equal(practitioner.dataset.ccNativeTools, '0');
assert.equal(typeof practitioner.buttons['Strumenti e tracciabilità'], 'function');
assert.match(practitioner.inserted.join(''), /Come compilare/);
assert.equal(form('cc_practitioner_form.js', 'Healthcare Practitioner', ['Administrator'], {}).inserted.length, 0);

const invoice = form('cc_finance_form.js', 'Sales Invoice', ['CC Manager'],
  {name: 'SINV-1', docstatus: 1, patient_name: 'Mario Rossi', grand_total: 100,
    outstanding_amount: 40, currency: 'EUR', items: [{item_name: 'Seduta'}]});
assert.match(invoice.inserted.join(''), /Pagato/);
assert.match(invoice.inserted.join(''), /60,00/);
assert.match(invoice.inserted.join(''), /Come compilare/);
assert.equal(form('cc_finance_form.js', 'Sales Invoice', ['Administrator'], {}).inserted.length, 0);
const syntheticInvoice = form('cc_finance_form.js', 'Sales Invoice', ['CC Manager'],
  {name:'SINV-2',docstatus:2,customer:'CC-MVP-POS-synthetic',grand_total:100,
    outstanding_amount:100,items:[{item_name:'CC-HTTP-UAT0000001 Session'}]});
assert.match(syntheticInvoice.inserted.join(''), /Paziente dimostrativo POS/);
assert.doesNotMatch(syntheticInvoice.inserted.join(''), /Residuo<\/dt>/);

const supplierInvoice = form('cc_finance_form.js', 'Purchase Invoice', ['CC Finance'],
  {name: 'PINV-1', docstatus: 0, supplier_name: 'Professionista Alfa'});
assert.equal(supplierInvoice.labels.supplier, 'Professionista o fornitore');
assert.match(supplierInvoice.inserted.join(''), /Come compilare/);

const payment = form('cc_finance_form.js', 'Payment Entry', ['CC Finance'],
  {name: 'PAY-1', docstatus: 0, payment_type: 'Receive'});
assert.equal(payment.labels.mode_of_payment, 'Metodo di pagamento');
assert.match(payment.inserted.join(''), /Come compilare/);

const bank = form('cc_finance_form.js', 'Bank Transaction', ['CC Finance'],
  {name: 'BANK-1', docstatus: 0, deposit: 100, unallocated_amount: 100});
assert.equal(bank.labels.unallocated_amount, 'Da riconciliare');
assert.match(bank.inserted.join(''), /Come compilare/);

for (const [doctype, file, field, label] of [
  ['Appointment Type','cc_operational_form.js','default_duration','Durata (minuti)'],
  ['CC Center Service','cc_operational_form.js','center','Centro'],
  ['CC Package Template','cc_operational_form.js','units','Sedute incluse'],
  ['Item Price','cc_item_price_form.js','price_list_rate','Prezzo']]) {
  const result = form(file, doctype, ['CC Manager'], {name:'SYNTHETIC-1'});
  assert.equal(result.labels[field], label);
  assert.match(result.inserted.join(''), /Come compilare/, `${doctype} native field guidance`);
}
const item = form('cc_item_form.js', 'Item', ['CC Manager'],
  {name:'ITEM-1', item_name:'Seduta', item_group:'Servizi', is_stock_item:0});
assert.equal(item.labels.item_name, 'Nome servizio');
assert.match(item.heatmap.html, /Movimenti di magazzino/);
assert.match(item.heatmap.html, /href="\/app\/query-report\/Stock Ledger"/);
assert.match(item.options.uom_help_html, /12 pezzi/);
assert.match(item.inserted.join(''), /Come compilare/);

console.log('native UX forms: PASS');
