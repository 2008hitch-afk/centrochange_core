/* Client-facing Desk navigation. Authorization remains on the server. */
(function () {
  "use strict";
  const clientRoles = ["CC Manager", "CC Secretariat", "CC Finance", "CC Accountant", "CC Professional"];
  const technicalRoles = ["System Manager", "Website Manager"];
  const home = roles => `/app/cc-unified-desk?cc_view=${["CC Manager", "CC Secretariat", "CC Professional"].some(role => roles.has(role)) ? "agenda" : "finance"}`;
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
      {title: "Panoramica", links: [["Inizio", home(roles), "chart-bar", true]]},
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
        ["Registro modifiche", desk("audit"), "history", manager]
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
  let lastRenderedRoute = "";
  function render() {
    const user = window.frappe?.session?.user;
    const roles = new Set(window.frappe?.user_roles || []);
    if (!user || user === "Guest" || user === "Administrator" || !clientRoles.some(role => roles.has(role)) || technicalRoles.some(role => roles.has(role))) {
      document.body.classList.remove("cc-client-desk");
      delete document.body.dataset.ccFormType;
      delete document.body.dataset.ccTechnical;
      document.getElementById("cc-desk-global-nav")?.remove();
      document.getElementById("cc-desk-sidebar")?.remove();
      return;
    }
    document.body.classList.add("cc-client-desk");
    lastRenderedRoute = location.pathname + location.search;
    const host = document.querySelector("body > .main-section");
    if (!host) return;
    let nav = document.getElementById("cc-desk-global-nav");
    let sidebar = document.getElementById("cc-desk-sidebar");
    if (!nav || !sidebar) {
      // Frappe v16 Desk uses a flex body. A direct body child consumes a
      // horizontal flex track and compresses every native Page/List/Form.
      nav = document.createElement("header");
      nav.id = "cc-desk-global-nav";
      nav.className = "cc-topbar d-print-none";
      sidebar = document.createElement("aside");
      sidebar.id = "cc-desk-sidebar";
      sidebar.className = "cc-primary-sidebar d-print-none";
      host.prepend(nav);
      host.prepend(sidebar);
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
    brand.className = "cc-desk-brand";
    brand.href = home(roles);
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
      list.className = "cc-sidebar-links";
      for (const [label, href, image] of group.links) {
        const anchor = document.createElement("a");
        anchor.className = "cc-sidebar-link";
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
    heading.innerHTML = '<span></span>';
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

    };
    mobileToggle.onclick = () => {
      const show = sidebar.classList.toggle("show");
      mobileToggle.setAttribute("aria-expanded", show ? "true" : "false");
      mobileToggle.setAttribute("aria-label", show ? "Chiudi navigazione" : "Apri navigazione");
    };
    const route = nativeRoute();
    document.body.classList.toggle("cc-native-view", Boolean(route));
    const pathParts = location.pathname.split("/").filter(Boolean);
    const routeIndex = pathParts.indexOf(route);
    document.body.dataset.ccFormType = routeIndex >= 0 && pathParts[routeIndex + 1] ? route : "";
    if (route !== "item") delete document.body.dataset.ccTechnical;
    if (route) document.title = `${nativeLabels[route]} · Centro Change`;
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
  // Delegate sidebar navigation to Frappe's router. Native anchors otherwise
  // trigger a full document request from the dedicated Page on pinned v16.
  document.addEventListener("click", event => {
    const link = event.target.closest?.("#cc-desk-sidebar a[href], #cc-desk-global-nav a[href]");
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.target) return;
    const url = new URL(link.href, location.href);
    if (url.origin !== location.origin || !url.pathname.startsWith("/app/")) return;
    event.preventDefault();
    event.stopPropagation();
    if (url.pathname === "/app/cc-unified-desk" && /^\/(?:app|desk)\/cc-unified-desk$/.test(location.pathname) && window.ccDeskNavigate)
      window.ccDeskNavigate(url.pathname + url.search);
    else {
      // Frappe keeps route_options across set_route calls unless explicitly
      // replaced; do not leak cc_view into a native List/Form URL.
      frappe.route_options = {};
      frappe.set_route(url.pathname + url.search);
    }
  }, true);
  // Frappe owns its List/Form DOM. Observe only direct shell replacement;
  // routing updates use Frappe's page-change event.
  let pending = false;
  const observer = new MutationObserver(() => {
    if (pending || !document.body.classList.contains("cc-client-desk")) return;
    pending = true;
    requestAnimationFrame(() => {
      pending = false;
      if (lastRenderedRoute !== location.pathname + location.search || !document.getElementById("cc-desk-global-nav") || !document.getElementById("cc-desk-sidebar")) render();
    });
  });
  observer.observe(document.body, {childList: true});
})();
