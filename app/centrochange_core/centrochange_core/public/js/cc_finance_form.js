/* Native accounting forms remain complete; only labels and titles change. */
(() => {
  if (window.__ccFinanceFormsRegistered) return;
  window.__ccFinanceFormsRegistered = true;
  const client = () => frappe.session.user !== "Administrator" &&
    (frappe.user_roles || []).some(role => ["CC Manager", "CC Secretariat", "CC Finance", "CC Accountant"].includes(role));
  const title = (frm, prefix) => frm.page.set_title(`${prefix} · ${frm.doc.name || "Nuovo"}`);
  frappe.ui.form.on("Sales Invoice", {refresh(frm) {
    if (!client()) return;
    title(frm, "Fattura paziente");
    if (frm.fields_dict.customer_section) frm.set_df_property("customer_section", "label", "Paziente e documento");
    if (frm.fields_dict.items_section) frm.set_df_property("items_section", "label", "Prestazioni");
    if (frm.fields_dict.payments_tab) frm.set_df_property("payments_tab", "label", "Pagamenti");
  }});
  frappe.ui.form.on("Purchase Invoice", {refresh(frm) {
    if (!client()) return;
    title(frm, "Fattura professionista");
    if (frm.fields_dict.supplier_invoice_details) frm.set_df_property("supplier_invoice_details", "label", "Documento del professionista");
    if (frm.fields_dict.payments_tab) frm.set_df_property("payments_tab", "label", "Pagamenti");
  }});
  frappe.ui.form.on("Payment Entry", {refresh(frm) {
    if (!client()) return;
    title(frm, "Incasso o pagamento");
    for (const [field, label] of Object.entries({type_of_payment:"Operazione",party_section:"Soggetto",
      payment_accounts_section:"Conti",payment_amounts_section:"Importi",transaction_references:"Riferimenti"})) {
      if (frm.fields_dict[field]) frm.set_df_property(field, "label", label);
    }
  }});
  frappe.ui.form.on("Bank Transaction", {refresh(frm) {
    if (!client()) return;
    title(frm, "Movimento bancario");
    const technical = Boolean(frm.__ccTechnicalOpen);
    frm.toggle_display(["cc_source_hash", "cc_source_key"], technical);
    frm.remove_custom_button("Riferimenti tecnici");
    frm.remove_custom_button("Nascondi riferimenti tecnici");
    frm.add_custom_button(technical ? "Nascondi riferimenti tecnici" : "Riferimenti tecnici", () => {
      frm.__ccTechnicalOpen = !technical;
      frm.toggle_display(["cc_source_hash", "cc_source_key"], frm.__ccTechnicalOpen);
      frm.remove_custom_button(technical ? "Nascondi riferimenti tecnici" : "Riferimenti tecnici");
      frm.trigger("refresh");
    });
  }});
})();
