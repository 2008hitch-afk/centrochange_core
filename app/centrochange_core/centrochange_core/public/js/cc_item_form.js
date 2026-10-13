/* Supported Item Form extension. No stored field or permission is changed. */
(() => {
  const client = () => frappe.session.user !== "Administrator" &&
    (frappe.user_roles || []).includes("CC Manager");
  const readable = value => String(value || "").replace(/^CC-HTTP-UAT\d+\s+/, "")
    .replace(/^Session$/i, "Seduta");
  const technicalTabs = ["accounting", "uom_tab", "item_tax_section_break", "inventory_section",
    "variants_section", "purchasing_tab", "sales_details", "manufacturing", "quality_tab"];
  const technicalSections = ["section_break_zlmj", "section_break_gjns", "section_break_znra"];
  const technicalFields = ["is_stock_item", "is_fixed_asset", "is_sales_item", "is_purchase_item",
    "allow_alternative_item", "has_variants", "is_customer_provided_item",
    "over_delivery_receipt_allowance", "over_billing_allowance"];
  function apply(frm) {
    if (!client()) return;
    const service = !frm.is_new() && !frm.doc.is_stock_item &&
      ["Servizi", "Services"].includes(frm.doc.item_group);
    const name = readable(frm.doc.item_name || frm.doc.name);
    if (name) frm.page.set_title(name);
    frm.set_df_property("item_name", "label", "Nome servizio");
    frm.set_df_property("item_group", "label", "Categoria");
    frm.set_df_property("description", "label", "Descrizione");
    frm.set_df_property("disabled", "label", "Disattivato");
    frm.set_df_property("details", "label", "Dettagli");
    frm.set_df_property("pricing_tab", "label", "Tariffe");
    frm.set_df_property("dashboard_tab", "label", "Collegamenti");
    const technical = !service || Boolean(frm.__ccTechnicalOpen);
    document.body.dataset.ccTechnical = technical ? "1" : "0";
    // In pinned Frappe 16.50, frm.set_df_property updates the document's
    // DocField copy but Layout.Tab owns another copy. Refresh the native Tab
    // controls explicitly, keeping the canonical Form and validation intact.
    for (const tab of frm.layout.tabs || []) {
      if (!technicalTabs.includes(tab.df.fieldname)) continue;
      if (tab.__ccOriginalHidden === undefined) tab.__ccOriginalHidden = tab.df.hidden;
      tab.df.hidden = technical ? tab.__ccOriginalHidden : 1;
      tab.refresh();
    }
    frm.layout.refresh_tabs();
    frm.toggle_display([...technicalSections, ...technicalFields, "brand", "item_name"], technical);
    frm.layout.sections.find(section => section.df.fieldname === "section_break_11")?.collapse(false);
    if (!service) return;
    frm.remove_custom_button("Dettagli tecnici");
    frm.remove_custom_button("Vista operativa");
    frm.add_custom_button(technical ? "Vista operativa" : "Dettagli tecnici", () => {
      frm.__ccTechnicalOpen = !technical;
      apply(frm);
    });
  }
  frappe.ui.form.on("Item", {refresh: apply});
})();
