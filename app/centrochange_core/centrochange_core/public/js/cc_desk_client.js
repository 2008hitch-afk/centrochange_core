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
  const nativeFieldLabels = {
    "Patient Name": "Nome paziente", patient_name: "Nome paziente",
    "Patient Demographics": "Dati del paziente", "Medical History": "Storia clinica",
    "Middle Name (optional)": "Secondo nome (facoltativo)",
    "Date of birth": "Data di nascita", "Identification Number (UID)": "Identificativo",
    "Report Preference": "Preferenza referto", "Customer Details": "Dati del soggetto fiscale",
    "Healthcare Practitioner": "Professionista", practitioner_name: "Nome professionista",
    "Mobile": "Cellulare", mobile: "Cellulare", "E-mail": "Email",
    "Item Name": "Servizio", item_name: "Servizio", "Item Code": "Codice servizio",
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
  const entries = roles => {
    const operate = ["CC Manager", "CC Secretariat", "CC Professional"].some(role => roles.has(role));
    const finance = ["CC Manager", "CC Secretariat", "CC Finance", "CC Accountant"].some(role => roles.has(role));
    const manager = roles.has("CC Manager");
    return [
      ["Inizio", home, true],
      ["Agenda", desk("agenda"), operate],
      ["Pazienti", manager ? "/app/patient" : `${desk("agenda")}&cc_ops_view=Pazienti`, operate],
      [manager ? "Professionisti" : "Disponibilità", manager ? "/app/healthcare-practitioner" : `${desk("agenda")}&cc_ops_view=Disponibilità`, operate],
      ["Finanza", desk("finance"), finance],
      ["Report", desk("professional"), finance],
      ["Notifiche", `${desk("agenda")}&cc_ops_view=Notifiche`, operate],
      ["Catalogo", "/app/item", manager],
      ["Registro modifiche", "/app/cc-audit-event", manager],
      ["Esci", "/api/method/logout", true]
    ].filter(([, , visible]) => visible);
  };
  function presentNativeTitle(route) {
    if (!route) return;
    const label = nativeLabels[route];
    const english = nativeEnglish[route];
    const parts = location.pathname.split("/").filter(Boolean);
    const form = parts.length > parts.indexOf(route) + 1 ? window.cur_frm : null;
    const personField = route === "patient" ? "patient_name" : route === "healthcare-practitioner" ? "practitioner_name" : null;
    const name = personField && form?.doc?.[personField];
    const personTitle = typeof name === "string" ? name.replace(/^CC-HTTP-UAT\d+\s+/, "").trim() : "";
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
    document.title = `${personTitle || label} · Centro Change`;
  }
  function render() {
    const user = window.frappe?.session?.user;
    const roles = new Set(window.frappe?.user_roles || []);
    if (!user || user === "Guest" || user === "Administrator" || !clientRoles.some(role => roles.has(role)) || technicalRoles.some(role => roles.has(role))) {
      document.body.classList.remove("cc-client-desk");
      document.getElementById("cc-desk-global-nav")?.remove();
      return;
    }
    document.body.classList.add("cc-client-desk");
    let nav = document.getElementById("cc-desk-global-nav");
    if (!nav) {
      // Frappe v16 Desk uses a flex body. A direct body child consumes a
      // horizontal flex track and compresses every native Page/List/Form.
      const host = document.querySelector("body > .main-section");
      if (!host) return;
      nav = document.createElement("nav");
      nav.id = "cc-desk-global-nav";
      nav.setAttribute("aria-label", "Navigazione Centro Change");
      host.prepend(nav);
    }
    const current = location.pathname + location.search;
    nav.replaceChildren();
    const brand = document.createElement("a");
    brand.className = "cc-desk-brand";
    brand.href = home;
    brand.textContent = "Centro Change";
    nav.append(brand);
    const links = document.createElement("div");
    links.className = "cc-desk-global-links";
    for (const [label, href] of entries(roles)) {
      const anchor = document.createElement("a");
      anchor.href = href;
      anchor.textContent = label;
      if (current === href || (href.includes("cc_view=") && current.startsWith(href + "&")) || (!href.includes("?") && location.pathname.startsWith(href + "/"))) anchor.setAttribute("aria-current", "page");
      links.append(anchor);
    }
    nav.append(links);
    const route = nativeRoute();
    if (route) {
      const context = document.createElement("span");
      context.className = "cc-desk-context";
      context.textContent = nativeLabels[route];
      nav.append(context);
      presentNativeTitle(route);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", render, {once: true});
  else render();
  if (window.jQuery) window.jQuery(document).on("toolbar_setup page-change", render);
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
    requestAnimationFrame(() => { pending = false; presentNativeTitle(nativeRoute()); });
  });
  observer.observe(document.body, {childList: true, subtree: true});
})();
