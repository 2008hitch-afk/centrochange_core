/* Existing native configuration forms, with customer-facing labels only. */
(() => {
  if (window.__ccOperationalFormsRegistered) return;
  window.__ccOperationalFormsRegistered = true;
  const client = () => frappe.session.user !== "Administrator" && (frappe.user_roles || []).includes("CC Manager");
  const readable = value => String(value || "").replace(/^CC-HTTP-UAT\d+\s+/, "").replace(/^Session$/i, "Seduta");
  frappe.ui.form.on("Appointment Type", {refresh(frm) {
    if (!client()) return;
    if (frm.doc.appointment_type) frm.page.set_title(readable(frm.doc.appointment_type));
    frm.set_df_property("appointment_type", "label", "Tipo di seduta");
    frm.set_df_property("default_duration", "label", "Durata (minuti)");
    frm.set_df_property("billing_tab", "label", "Tariffe");
    frm.set_df_property("medical_codes_tab", "label", "Codifiche");
  }});
  frappe.ui.form.on("CC Center Service", {refresh(frm) {
    if (!client()) return;
    frm.page.set_title(readable(frm.doc.appointment_type) || "Servizio del centro");
    frm.set_df_property("center", "label", "Centro");
    frm.set_df_property("appointment_type", "label", "Tipo di seduta");
    frm.set_df_property("enabled", "label", "Abilitato");
  }});
  frappe.ui.form.on("CC Package Template", {refresh(frm) {
    if (!client()) return;
    if (frm.doc.title) frm.page.set_title(frm.doc.title);
    frm.set_df_property("title", "label", "Nome pacchetto");
    frm.set_df_property("service_item", "label", "Servizio");
    frm.set_df_property("units", "label", "Sedute incluse");
    frm.set_df_property("enabled", "label", "Abilitato");
  }});
})();
