/* Existing native configuration forms, with customer-facing labels only. */
(() => {
  if (window.__ccOperationalFormsRegistered) return;
  window.__ccOperationalFormsRegistered = true;
  const client = () => frappe.session.user !== "Administrator" && (frappe.user_roles || []).includes("CC Manager");
  const readable = value => String(value || "").replace(/^CC-HTTP-UAT\d+\s+/, "").replace(/^Session$/i, "Seduta");
  function guidance(frm, text) {
    frm.page.main.find(".cc-native-help").remove();
    frm.page.main.find(".form-layout").first().before('<section class="cc-native-help" aria-label="Guida alla compilazione"><strong>Come compilare</strong><span>'+text+' I campi con * sono obbligatori. Usa Salva per confermare e correggi i campi segnalati in caso di errore.</span></section>');
  }
  frappe.ui.form.on("Appointment Type", {refresh(frm) {
    if (!client()) return;
    if (frm.doc.appointment_type) frm.page.set_title(readable(frm.doc.appointment_type));
    frm.set_df_property("appointment_type", "label", "Tipo di seduta");
    frm.set_df_property("default_duration", "label", "Durata (minuti)");
    frm.set_df_property("billing_tab", "label", "Tariffe");
    frm.set_df_property("medical_codes_tab", "label", "Codifiche");
    guidance(frm,"Inserisci il nome e la durata della seduta nei campi qui sotto; verifica le tariffe e le codifiche se pertinenti.");
  }});
  frappe.ui.form.on("CC Center Service", {refresh(frm) {
    if (!client()) return;
    frm.page.set_title(readable(frm.doc.appointment_type) || "Servizio del centro");
    frm.set_df_property("center", "label", "Centro");
    frm.set_df_property("appointment_type", "label", "Tipo di seduta");
    frm.set_df_property("enabled", "label", "Abilitato");
    guidance(frm,"Seleziona il Centro e il tipo di seduta. Attiva solo i servizi effettivamente disponibili in questa sede.");
  }});
  frappe.ui.form.on("CC Package Template", {refresh(frm) {
    if (!client()) return;
    if (frm.doc.title) frm.page.set_title(frm.doc.title);
    frm.set_df_property("title", "label", "Nome pacchetto");
    frm.set_df_property("service_item", "label", "Servizio");
    frm.set_df_property("units", "label", "Sedute incluse");
    frm.set_df_property("enabled", "label", "Abilitato");
    guidance(frm,"Inserisci nome, servizio e numero di sedute comprese nel pacchetto.");
  }});
})();
