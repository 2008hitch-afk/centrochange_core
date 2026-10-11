const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../app/centrochange_core/centrochange_core/public/js/cc_desk_client.js'), 'utf8');

function check(user, roles, expected, absent, route = '/app/cc-unified-desk?cc_view=home') {
  const registry = new Map();
  class Element {
    constructor(tag) { this.tagName = tag; this.children = []; this.attributes = {}; this.className = ''; this.textContent = ''; }
    append(...nodes) { this.children.push(...nodes); for (const node of nodes) if (node.id) registry.set(node.id, node); }
    prepend(node) { this.children.unshift(node); if (node.id) registry.set(node.id, node); }
    replaceChildren(...nodes) { this.children = nodes; }
    setAttribute(name, value) { this.attributes[name] = value; }
    remove() { if (this.id) registry.delete(this.id); }
  }
  const classes = new Set();
  const document = {
    readyState: 'complete',
    body: new Element('body'),
    createElement: tag => new Element(tag),
    getElementById: id => registry.get(id),
  };
  document.body.classList = {add: value => classes.add(value), remove: value => classes.delete(value)};
  const [pathname, search = ''] = route.split('?');
  vm.runInNewContext(source, {window: {frappe: {session: {user}, user_roles: roles}}, document, location: {pathname, search: search ? '?' + search : ''}});
  const nav = registry.get('cc-desk-global-nav');
  if (expected === null) {
    assert.equal(nav, undefined);
    assert(!classes.has('cc-client-desk'));
    return;
  }
  assert(nav && classes.has('cc-client-desk'));
  const links = nav.children[1].children.map(node => node.textContent);
  for (const label of expected) assert(links.includes(label), `${user}: missing ${label}`);
  for (const label of absent) assert(!links.includes(label), `${user}: unexpected ${label}`);
  assert(!links.some(label => /Builder|Frappe|ERPNext|Sviluppatore/i.test(label)));
}

check('manager@example.invalid', ['CC Manager'], ['Inizio', 'Agenda', 'Pazienti', 'Professionisti', 'Finanza', 'Report', 'Catalogo', 'Registro modifiche'], []);
check('secretary@example.invalid', ['CC Secretariat'], ['Agenda', 'Pazienti', 'Disponibilità', 'Finanza'], ['Catalogo', 'Registro modifiche']);
check('finance@example.invalid', ['CC Finance'], ['Finanza', 'Report'], ['Agenda', 'Catalogo', 'Pazienti']);
check('accountant@example.invalid', ['CC Accountant'], ['Finanza', 'Report'], ['Agenda', 'Catalogo']);
check('professional@example.invalid', ['CC Professional'], ['Agenda', 'Pazienti', 'Disponibilità'], ['Finanza', 'Report', 'Catalogo']);
check('Administrator', ['System Manager', 'CC Manager'], null, []);
check('guest', [], null, []);
console.log('C109 Desk shell offline role/menu checks: PASS (7 profiles)');
