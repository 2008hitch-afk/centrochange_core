// Offline Desk entry test. It does not start Frappe, Docker or a browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(
  'app/centrochange_core/centrochange_core/centro_change_core/page/cc_unified_desk/cc_unified_desk.js',
  'utf8',
);

function entry(roles, search = '') {
  const root = {
    childElementCount: 0,
    addEventListener() {},
    replaceChildren(...children) {
      this.children = children;
      this.childElementCount = children.length;
    },
  };
  const page = {main: {}, set_title(title) {this.title = title;}};
  const element = () => ({
    children: [],
    append(...children) {this.children.push(...children);},
    prepend(...children) {this.children.unshift(...children);},
    setAttribute() {},
  });
  const context = {
    URL, URLSearchParams,
    location: {origin: 'http://localhost:8109', href: 'http://localhost:8109/app/cc-unified-desk' + search, search},
    history: {replaceState(_state, _title, url) {this.url = url;}},
    document: {querySelector: () => true, createElement: element, body: {classList: {remove() {}}}},
    window: {},
    frappe: {pages: {'cc-unified-desk': {}}, user_roles: roles, csrf_token: 'synthetic',
      ui: {make_app_page: () => page}},
    $: () => ({0: root, appendTo: () => [root], on() {}}),
  };
  vm.runInNewContext(source, context);
  context.frappe.pages['cc-unified-desk'].on_page_load({});
  context.frappe.pages['cc-unified-desk'].on_page_show();
  const surface = root.children[0];
  const demo = surface.children[0].textContent;
  const nav = surface.children[1].innerHTML;
  const home = surface.children[2].innerHTML;
  return {demo, nav, home, title: page.title, url: context.history.url};
}

const professional = entry(['CC Professional']);
assert.match(professional.home, /Agenda/);
assert.match(professional.home, /cc_ops_view=Disponibilit%C3%A0/);
assert.doesNotMatch(professional.home, /Fatture pazienti|Registro modifiche/);
assert.match(professional.url, /cc_view=home/);
assert.match(professional.title, /Centro Change · Inizio/);
assert.match(professional.demo, /Versione dimostrativa/);

const manager = entry(['CC Manager']);
assert.match(manager.home, /Anagrafiche pazienti/);
assert.match(manager.home, /Finanza/);
assert.match(manager.home, /Registro modifiche/);
assert.match(manager.home, /cc_fin_view=Banca/);
assert.match(manager.nav, /aria-current="page"/);

const unknown = entry(['CC Finance'], '?cc_view=__proto__');
assert.match(unknown.home, /Finanza/);
assert.doesNotMatch(unknown.home, /Anagrafiche pazienti/);
assert.match(unknown.url, /cc_view=home/);
console.log('C109 Desk home: 3 role/route checks PASS');
