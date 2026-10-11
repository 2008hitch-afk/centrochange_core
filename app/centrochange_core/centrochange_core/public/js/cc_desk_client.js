/* Client-facing Desk navigation. Authorization remains on the server. */
(function () {
  "use strict";
  const clientRoles = ["CC Manager", "CC Secretariat", "CC Finance", "CC Accountant", "CC Professional"];
  const technicalRoles = ["System Manager", "Website Manager"];
  const home = "/app/cc-unified-desk?cc_view=home";
  const desk = view => `/app/cc-unified-desk?cc_view=${view}`;
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
      ["Catalogo", "/app/item", manager],
      ["Registro modifiche", "/app/cc-audit-event", manager]
    ].filter(([, , visible]) => visible);
  };
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
      nav = document.createElement("nav");
      nav.id = "cc-desk-global-nav";
      nav.setAttribute("aria-label", "Navigazione Centro Change");
      document.body.prepend(nav);
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
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", render, {once: true});
  else render();
  if (window.jQuery) window.jQuery(document).on("toolbar_setup page-change", render);
})();
