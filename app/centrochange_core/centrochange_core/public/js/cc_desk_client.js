/* Client-facing Desk navigation. Authorization remains on the server. */
(function () {
  "use strict";
  const clientRoles = ["CC Manager", "CC Secretariat", "CC Finance", "CC Accountant", "CC Professional"];
  const technicalRoles = ["System Manager", "Website Manager"];
  const home = "/app/cc-unified-desk?cc_view=home";
  const desk = view => `/app/cc-unified-desk?cc_view=${view}`;
  // These labels change presentation only. Native DocPerm and the CC guards
  // remain authoritative for every direct route and API request.
  const nativeLabels = {
    patient: "Pazienti", "healthcare-practitioner": "Professionisti",
    item: "Servizi", "item-price": "Tariffe", "appointment-type": "Tipi di seduta",
    "cc-center-service": "Servizi del centro", "cc-package-template": "Modelli pacchetto",
    "sales-invoice": "Fatture pazienti", "purchase-invoice": "Fatture professionisti",
    "payment-entry": "Incassi e pagamenti", "bank-transaction": "Movimenti bancari",
    "cc-audit-event": "Registro modifiche"
  };
  const nativeEnglish = {
    patient: "Patient", "healthcare-practitioner": "Healthcare Practitioner",
    item: "Item", "item-price": "Item Price", "appointment-type": "Appointment Type",
    "cc-center-service": "CC Center Service", "cc-package-template": "CC Package Template",
    "sales-invoice": "Sales Invoice", "purchase-invoice": "Purchase Invoice",
    "payment-entry": "Payment Entry", "bank-transaction": "Bank Transaction",
    "cc-audit-event": "CC Audit Event"
  };
  const nativeRenderedTitles = {
    patient: ["Paziente"], "healthcare-practitioner": ["Professionista"],
    item: ["Servizio / articolo", "Articolo"], "item-price": ["Prezzo articolo"],
    "sales-invoice": ["Fattura di vendita"], "purchase-invoice": ["Fattura di acquisto"],
    "payment-entry": ["Registrazione pagamento"], "bank-transaction": ["Transazione bancaria"]
  };
  const nativeFieldLabels = {
    "Patient Name": "Nome paziente", patient_name: "Nome paziente",
    "Patient Demographics": "Dati del paziente", "Medical History": "Storia clinica",
    "Middle Name (optional)": "Secondo nome (facoltativo)",
    "Date of birth": "Data di nascita", "Identification Number (UID)": "Identificativo",
    "Report Preference": "Preferenza referto", "Customer Details": "Dati del soggetto fiscale",
    "Healthcare Practitioner": "Professionista", practitioner_name: "Nome professionista",
    "Mobile": "Cellulare", mobile: "Cellulare", "E-mail": "Email",
    "Item Name": "Servizio", item_name: "Servizio", "Item Code": "Codice servizio",
    "Medical Department": "Reparto", "Designation": "Qualifica", "Item Group": "Categoria",
    "Variant Of": "Variante di", "Has Variants": "Ha varianti", "Purpose": "Uso",
    "UOM": "Unità", "Phone (Office)": "Telefono ufficio", "Created On": "Creato il",
    "Bank Account": "Conto bancario", "Deposit": "Entrata", "Withdrawal": "Uscita",
    "Posting Date": "Data contabile", "Due Date": "Scadenza",
    "Grand Total": "Totale", "Outstanding Amount": "Residuo",
    "Customer": "Soggetto fiscale", "Supplier": "Fornitore",
    "Status": "Stato", "Modified": "Modificato", "Owner": "Creato da",
    "DEV Fiscal Profile": "Profilo fiscale di prova", "Centro Change Center": "Centro",
    "Company Tax ID": "Partita IVA aziendale", "Posting Time": "Ora di registrazione",
    "Dashboard": "Riepilogo", "Address & Contact": "Indirizzo e contatti",
    "Medical": "Dati sanitari", "Payments": "Pagamenti", "Terms": "Condizioni",
    "More Info": "Altre informazioni", "Save": "Salva", "New": "Nuovo",
    "Use scoped Centro Change accounting reports": "Usa i report contabili autorizzati di Centro Change"
  };
  function nativeRoute() {
    const parts = location.pathname.split("/").filter(Boolean);
    if (!parts.includes("app") && !parts.includes("desk")) return null;
    return parts.find(part => Object.hasOwn(nativeLabels, part)) || null;
  }
  const menu = roles => {
    const operate = ["CC Manager", "CC Secretariat", "CC Professional"].some(role => roles.has(role));
    const finance = ["CC Manager", "CC Secretariat", "CC Finance", "CC Accountant"].some(role => roles.has(role));
    const manager = roles.has("CC Manager");
    const professional = roles.has("CC Professional") && !manager;
    const accountant = roles.has("CC Accountant") && !manager;
    return [
      {title: "Panoramica", links: [["Inizio", home, "chart-bar", true]]},
      {title: "Operatività", links: [
        ["Agenda", desk("agenda"), "calendar-week", operate],
        ["Ricerca pazienti", `${desk("agenda")}&cc_ops_view=Pazienti`, "users", operate],
        ["Anagrafica pazienti", "/app/patient", "users", manager],
        ["Anagrafica professionisti", "/app/healthcare-practitioner", "users", manager],
        ["Disponibilità", `${desk("agenda")}&cc_ops_view=Disponibilità`, "clock", operate],
        ["Notifiche", `${desk("agenda")}&cc_ops_view=Notifiche`, "bell", operate]
      ]},
      {title: "Amministrazione", links: [
        ["Finanza", desk("finance"), "wallet", finance],
        ["Fatture pazienti", "/app/sales-invoice", "receipt", finance],
        ["Fatture professionisti", "/app/purchase-invoice", "file-invoice", finance],
        ["Incassi e pagamenti", "/app/payment-entry", "wallet", finance && !accountant],
        ["Movimenti bancari", "/app/bank-transaction", "building-bank", finance && !accountant],
        ["Banca", `${desk("finance")}&cc_fin_view=Banca`, "building-bank", finance && !accountant],
        ["SdI simulato", `${desk("finance")}&cc_fin_view=SdI`, "send", finance && !accountant],
        ["TS simulato", `${desk("finance")}&cc_fin_view=TS`, "shield-check", finance && !accountant]
      ]},
      {title: "Report", links: [
        ["Report professionisti", desk("professional"), "chart-bar", finance],
        ["Report economico pazienti", desk("patient"), "chart-bar", finance]
      ]},
      {title: "Gestione", links: [
        ["Gestione accessi", `${desk("agenda")}&cc_ops_view=Gestione%20accessi`, "settings", manager],
        ["Servizi", "/app/item", "list-check", manager],
        ["Tariffe", "/app/item-price", "receipt", manager],
        ["Tipi di seduta", "/app/appointment-type", "calendar-week", manager],
        ["Servizi del centro", "/app/cc-center-service", "list-check", manager],
        ["Modelli pacchetto", "/app/cc-package-template", "list-check", manager],
        ["Registro modifiche", "/app/cc-audit-event", "history", manager]
      ]}
    ].map(group => ({...group, links: group.links.filter(([, , , visible]) => visible)}))
      .filter(group => group.links.length && !(professional && ["Amministrazione", "Report", "Gestione"].includes(group.title)));
  };
  const icon = name => `/assets/centrochange_core/vendor/tabler-icons-3.35.0/${name}.svg`;
  function active(href) {
    const url = new URL(href, location.origin);
    if (url.pathname.startsWith("/app/") && !url.search && nativeRoute() === url.pathname.split("/").pop()) return true;
    if (url.pathname !== location.pathname && !(location.pathname.startsWith(url.pathname + "/") && !url.search)) return false;
    for (const [key, value] of url.searchParams) if (new URLSearchParams(location.search).get(key) !== value) return false;
    if (url.pathname === "/app/cc-unified-desk" && !url.searchParams.has("cc_ops_view") && !url.searchParams.has("cc_fin_view")) {
      const current = new URLSearchParams(location.search);
      if (current.has("cc_ops_view") || current.has("cc_fin_view")) return false;
    }
    return true;
  }
  function roleLabel(roles) {
    return [["CC Manager", "Direzione"], ["CC Secretariat", "Segreteria"], ["CC Professional", "Professionista"],
      ["CC Finance", "Finance"], ["CC Accountant", "Commercialista"]].find(([role]) => roles.has(role))?.[1] || "Centro Change";
  }
  function accountName(user) {
    const full = typeof window.frappe?.user?.full_name === "function" ? window.frappe.user.full_name() : user;
    const demo = /^CC-HTTP-UAT\d+\s+([a-z])$/.exec(full || "");
    if (!demo) return full || user;
    return ({m: "Demo Direzione", s: "Demo Segreteria", a: "Demo professionista Alfa",
      b: "Demo professionista Beta", c: "Demo professionista C", f: "Demo Finance",
      t: "Demo Commercialista"})[demo[1]] || "Account demo";
  }
  function presentNativeTitle(route) {
    if (!route) return;
    const label = nativeLabels[route];
    const english = nativeEnglish[route];
    const parts = location.pathname.split("/").filter(Boolean);
    const form = parts.length > parts.indexOf(route) + 1 ? window.cur_frm : null;
    const personField = route === "patient" ? "patient_name" : route === "healthcare-practitioner" ? "practitioner_name" : null;
    const name = personField && form?.doc?.[personField];
    const readablePerson = value => {
      const short = value.replace(/^CC-HTTP-UAT\d+\s+/, "").trim();
      if (route === "healthcare-practitioner") return ({a: "Professionista Alfa", b: "Professionista Beta", c: "Professionista Gamma"})[short] || short;
      return short;
    };
    const personTitle = typeof name === "string" ? readablePerson(name) : "";
    for (const node of document.querySelectorAll(".page-head .title-text, .page-head .page-title, .page-head .breadcrumb-item")) {
      // Never replace a document name, field value or user-entered text.
      if (node.children.length === 0 && [english, route, route.replaceAll("-", " ")].includes(node.textContent.trim())) node.textContent = label;
      else if (personTitle && form?.doctype === english && node.children.length === 0 && node.textContent.trim() === form.doc.name) {
        node.title = form.doc.name; // canonical identity remains available for traceability
        node.textContent = personTitle;
      }
    }
    for (const node of document.querySelectorAll(".list-row-head .list-row-col, .form-page .control-label, .form-page .section-head, .form-page .nav-link, .form-page .form-section .section-head")) {
      if (node.children.length === 0) {
        const translation = nativeFieldLabels[node.textContent.trim()];
        if (translation) node.textContent = translation;
      }
    }
    const listTerms = {"Filters": "Filtri", "Filter": "Filtro", "Purpose": "Utilizzo", "UOM": "Unità", "Item Group": "Categoria", "Item Type": "Tipo servizio", "Medical Department": "Reparto", "Designation": "Qualifica", "Phone (Office)": "Telefono ufficio", "Bank Account": "Conto bancario", "Deposit": "Entrata", "Withdrawal": "Uscita", "Description": "Descrizione", "Tag": "Etichette", "Sales & Purchase": "Vendita e acquisto", "Nos": "Pezzi", "Paid": "Pagata", "Partly Paid": "Pagata parzialmente", "Unreconciled": "Da riconciliare", "Reconciled": "Riconciliata", "Submitted": "Confermata", "Draft": "Bozza"};
    for (const root of document.querySelectorAll('.list-row-head, .list-row, .page-form, .page-head .page-actions, .form-sidebar')) {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        const original = node.nodeValue;
        const trimmed = original.trim();
        if (listTerms[trimmed]) node.nodeValue = original.replace(trimmed, listTerms[trimmed]);
        else if (root.classList.contains('form-sidebar') && original.includes('Last Edited By')) node.nodeValue = original.replace('Last Edited By', 'Ultima modifica di');
        else if (root.classList.contains('form-sidebar') && original.includes('Assign')) node.nodeValue = original.replace('Assign', 'Assegna');
        else if (root.classList.contains('form-sidebar') && original.includes('Tags')) node.nodeValue = original.replace('Tags', 'Etichette');
      }
    }
    if (personTitle && form?.doc?.name) {
      for (const node of document.querySelectorAll('.page-head .es-breadcrumbs__label, .form-sidebar .sidebar-stat')) {
        if (node.children.length === 0 && node.textContent.trim() === form.doc.name) {
          node.title = form.doc.name;
          node.textContent = personTitle;
        }
      }
      const sidebar = document.querySelector('.form-sidebar');
      if (sidebar) {
        const walker = document.createTreeWalker(sidebar, NodeFilter.SHOW_TEXT);
        let node;
        while ((node = walker.nextNode())) {
          if (node.nodeValue.trim() === form.doc.name || node.nodeValue.trim() === name) {
            node.parentElement.title = form.doc.name;
            node.nodeValue = node.nodeValue.replace(node.nodeValue.trim(), personTitle);
          }
        }
      }
    }
    // The demo fixture prefixes readable names with a synthetic import key.
    // Keep the canonical value in href, data-name and title for traceability.
    for (const node of document.querySelectorAll('.list-row .list-subject a[data-name], .list-row [data-fieldname="item_name"] a[data-name]')) {
      const canonical = node.getAttribute("data-name") || "";
      const displayed = node.textContent.trim();
      if (/^CC-HTTP-UAT\d+\s+\S/.test(displayed)) {
        node.title = `${displayed} · ${canonical}`;
        node.textContent = readablePerson(displayed);
      } else if (route === "bank-transaction" && /^CC DEV CC-HTTP-UAT\d+\s+[A-Z](?: - CC SYNTHETIC BANK)?$/.test(displayed)) {
        node.title = displayed;
        node.textContent = `Conto Centro ${displayed.match(/CC-HTTP-UAT\d+\s+([A-Z])/)?.[1]}`;
      }
    }
    if (route === "bank-transaction") {
      for (const node of document.querySelectorAll('.list-row [data-fieldname="bank_account"] a, .list-row .list-subject a')) {
        const original = node.textContent.trim();
        if (/^CC DEV CC-HTTP-UAT\d+\s+[A-Z](?: - CC SYNTHETIC BANK)?$/.test(original)) {
          node.title = original;
          node.textContent = `Conto Centro ${original.match(/CC-HTTP-UAT\d+\s+([A-Z])/)?.[1]}`;
        }
      }
      for (const node of document.querySelectorAll('.list-row [data-fieldname="description"] a, .list-row [data-fieldname="description"] .ellipsis')) {
        if (node.children.length || !/^SYNTHETIC UAT\s+/i.test(node.textContent.trim())) continue;
        const original = node.textContent.trim();
        node.title = original;
        const clean = original.replace(/^SYNTHETIC UAT\s+/i, "");
        node.textContent = clean.charAt(0).toLocaleUpperCase("it-IT") + clean.slice(1);
      }
    }
    for (const input of document.querySelectorAll('.list-page-form input[placeholder]')) {
      const label = input.placeholder === "Nome e Cognome" ? (route === "healthcare-practitioner" ? "Nome professionista" : "Nome paziente") :
        nativeFieldLabels[input.placeholder] || ({"Medical Department": "Reparto", "Designation": "Qualifica", "Variant Of": "Variante di", "Item Group": "Categoria", "Item Name": "Servizio", "Nome articolo": "Nome servizio"})[input.placeholder];
      if (label) input.placeholder = label;
    }
    for (const node of document.querySelectorAll('.page-head .es-breadcrumbs__label, .page-head .es-breadcrumbs__item')) {
      if (node.children.length === 0 && [english, route, route.replaceAll("-", " "), ...(nativeRenderedTitles[route] || [])].includes(node.textContent.trim())) node.textContent = label;
    }
    document.querySelectorAll('.page-head').forEach(node => node.classList.add('page-header'));
    document.querySelectorAll('.page-container').forEach(node => node.classList.add('page-body'));
    document.title = `${personTitle || label} · Centro Change`;
  }
  let lastRenderedRoute = "";
  function render() {
    const user = window.frappe?.session?.user;
    const roles = new Set(window.frappe?.user_roles || []);
    if (!user || user === "Guest" || user === "Administrator" || !clientRoles.some(role => roles.has(role)) || technicalRoles.some(role => roles.has(role))) {
      document.body.classList.remove("cc-client-desk");
      document.getElementById("cc-desk-global-nav")?.remove();
      document.getElementById("cc-desk-sidebar")?.remove();
      return;
    }
    document.body.classList.add("cc-client-desk");
    lastRenderedRoute = location.pathname + location.search;
    const host = document.querySelector("body > .main-section");
    if (!host) return;
    host.classList.add("page");
    host.querySelector(":scope > #body")?.classList.add("page-wrapper");
    let nav = document.getElementById("cc-desk-global-nav");
    let sidebar = document.getElementById("cc-desk-sidebar");
    if (!nav || !sidebar) {
      // Frappe v16 Desk uses a flex body. A direct body child consumes a
      // horizontal flex track and compresses every native Page/List/Form.
      nav = document.createElement("header");
      nav.id = "cc-desk-global-nav";
      nav.className = "navbar d-print-none";
      sidebar = document.createElement("aside");
      sidebar.id = "cc-desk-sidebar";
      sidebar.className = "navbar navbar-vertical d-print-none";
      host.prepend(nav);
      host.prepend(sidebar);
    }
    if (!document.getElementById("cc-tabler-core")) {
      // The pinned Tabler stylesheet is a low-priority layer so Frappe's
      // unlayered native List/Form styles retain their supported behavior.
      const style = document.createElement("style");
      style.id = "cc-tabler-core";
      style.textContent = '@import url("/assets/centrochange_core/vendor/tabler-core-1.6.1/tabler.min.css") layer(cc-tabler);';
      document.head.append(style);
    }
    const groups = menu(roles);
    const currentLink = groups.flatMap(group => group.links).find(([, href]) => active(href));
    const title = currentLink?.[0] || nativeLabels[nativeRoute()] || "Centro Change";
    const isMobile = window.matchMedia("(max-width: 991.98px)").matches;
    const expanded = sidebar.classList.contains("show");
    sidebar.replaceChildren();
    const brandRow = document.createElement("div");
    brandRow.className = "cc-sidebar-heading";
    const brand = document.createElement("a");
    brand.className = "navbar-brand cc-desk-brand";
    brand.href = home;
    brand.textContent = "Centro Change";
    brandRow.append(brand);
    const collapse = document.createElement("button");
    collapse.type = "button";
    collapse.className = "btn btn-ghost-secondary cc-sidebar-collapse";
    collapse.setAttribute("aria-label", "Riduci menu");
    collapse.setAttribute("aria-controls", "cc-desk-sidebar-menu");
    collapse.setAttribute("aria-expanded", document.body.classList.contains("cc-sidebar-compact") ? "false" : "true");
    collapse.innerHTML = `<img src="${icon("menu-2")}" alt="">`;
    brandRow.append(collapse);
    sidebar.append(brandRow);
    const links = document.createElement("nav");
    links.id = "cc-desk-sidebar-menu";
    links.className = "cc-sidebar-menu";
    links.setAttribute("aria-label", "Navigazione principale");
    for (const group of groups) {
      const collapsible = ["Amministrazione", "Gestione"].includes(group.title);
      const section = document.createElement(collapsible ? "details" : "section");
      section.className = "cc-sidebar-group";
      if (collapsible) section.open = group.links.some(([, href]) => active(href)) ||
        (group.title === "Amministrazione" && !roles.has("CC Manager"));
      const heading = document.createElement(collapsible ? "summary" : "h2");
      heading.className = "cc-sidebar-group-title";
      heading.textContent = group.title;
      section.append(heading);
      const list = document.createElement("div");
      list.className = "navbar-nav";
      for (const [label, href, image] of group.links) {
        const anchor = document.createElement("a");
        anchor.className = "nav-link cc-sidebar-link";
        anchor.href = href;
        anchor.title = label;
        anchor.innerHTML = `<span class="nav-link-icon"><img src="${icon(image)}" alt=""></span><span class="nav-link-title"></span>`;
        anchor.querySelector(".nav-link-title").textContent = label;
        if (active(href)) {
          anchor.classList.add("active");
          anchor.setAttribute("aria-current", "page");
        }
        list.append(anchor);
      }
      section.append(list);
      links.append(section);
    }
    sidebar.append(links);
    if (expanded && isMobile) sidebar.classList.add("show");
    nav.replaceChildren();
    const mobileToggle = document.createElement("button");
    mobileToggle.type = "button";
    mobileToggle.className = "btn btn-ghost-secondary cc-mobile-toggle";
    mobileToggle.setAttribute("aria-label", "Apri navigazione");
    mobileToggle.setAttribute("aria-controls", "cc-desk-sidebar-menu");
    mobileToggle.setAttribute("aria-expanded", expanded ? "true" : "false");
    mobileToggle.innerHTML = `<img src="${icon("menu-2")}" alt="">`;
    nav.append(mobileToggle);
    const heading = document.createElement("div");
    heading.className = "cc-navbar-identity";
    heading.innerHTML = '<strong>Centro Change</strong><span></span>';
    heading.querySelector("span").textContent = title;
    nav.append(heading);
    if (["CC Manager", "CC Secretariat", "CC Professional"].some(role => roles.has(role))) {
      const notifications = document.createElement("a");
      notifications.className = "btn btn-ghost-secondary cc-navbar-notifications";
      notifications.href = `${desk("agenda")}&cc_ops_view=Notifiche`;
      notifications.setAttribute("aria-label", "Notifiche");
      notifications.innerHTML = `<img src="${icon("bell")}" alt="">`;
      nav.append(notifications);
    }
    const account = document.createElement("details");
    account.className = "cc-navbar-account";
    const summary = document.createElement("summary");
    summary.className = "btn btn-ghost-secondary";
    summary.textContent = `${accountName(user)} · ${roleLabel(roles)}`;
    account.append(summary);
    const logout = document.createElement("a");
    logout.href = "/api/method/logout";
    logout.textContent = "Esci";
    logout.className = "dropdown-item";
    account.append(logout);
    nav.append(account);
    collapse.onclick = () => {
      const compact = document.body.classList.toggle("cc-sidebar-compact");
      collapse.setAttribute("aria-expanded", compact ? "false" : "true");
      try { localStorage.setItem("cc-sidebar-compact", compact ? "1" : "0"); } catch (_) {}
    };
    mobileToggle.onclick = () => {
      const show = sidebar.classList.toggle("show");
      mobileToggle.setAttribute("aria-expanded", show ? "true" : "false");
      mobileToggle.setAttribute("aria-label", show ? "Chiudi navigazione" : "Apri navigazione");
    };
    if (!document.body.dataset.ccSidebarReady) {
      document.body.dataset.ccSidebarReady = "1";
      try { if (localStorage.getItem("cc-sidebar-compact") === "1") document.body.classList.add("cc-sidebar-compact"); } catch (_) {}
    }
    const route = nativeRoute();
    document.body.classList.toggle("cc-native-view", Boolean(route));
    if (route) {
      presentNativeTitle(route);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", render, {once: true});
  else render();
  if (window.jQuery) window.jQuery(document).on("toolbar_setup page-change", render);
  window.addEventListener("cc-desk-route-change", render);
  document.addEventListener("click", async event => {
    const link = event.target.closest?.("#cc-desk-global-nav a[href='/api/method/logout']");
    if (!link) return;
    event.preventDefault();
    try {
      const response = await fetch(link.href, {method: "POST", credentials: "same-origin", headers: {"X-Frappe-CSRF-Token": window.frappe?.csrf_token || ""}});
      if (!response.ok) throw new Error("logout failed");
      location.href = "/login?redirect-to=/app/cc-unified-desk";
    } catch (_) { window.frappe?.msgprint?.("Impossibile uscire. Riprova."); }
  });
  // Native List/Form headings are mounted after Desk's route event. A bounded
  // observer updates only known heading nodes, never record content.
  let pending = false;
  const observer = new MutationObserver(() => {
    if (pending || !document.body.classList.contains("cc-client-desk")) return;
    pending = true;
    requestAnimationFrame(() => {
      pending = false;
      if (lastRenderedRoute !== location.pathname + location.search || !document.getElementById("cc-desk-global-nav") || !document.getElementById("cc-desk-sidebar")) render();
      else presentNativeTitle(nativeRoute());
    });
  });
  observer.observe(document.body, {childList: true, subtree: true});
})();
