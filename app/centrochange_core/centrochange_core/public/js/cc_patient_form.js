/* Supported native Form Script: human title, canonical fields unchanged. */
frappe.ui.form.on("Patient", {
  refresh(frm) {
    if (frappe.session.user === "Administrator" || !(frappe.user_roles || []).some(role => role.startsWith("CC "))) return;
    const label=String(frm.doc.patient_name||"").replace(/^CC-HTTP-UAT\d+\s+/,"");
    if(label) frm.page.set_title(label);
    for(const [field,title] of Object.entries({basic_info:"Dati anagrafici",customer_details_section:"Dati amministrativi",
      more_info:"Altre informazioni",address_and_contact_tab:"Recapiti",medical_history_tab:"Storia clinica",
      patient_name:"Nome e cognome",sex:"Sesso",dob:"Data di nascita",uid:"Identificativo"})) {
      if(frm.fields_dict[field]) frm.set_df_property(field,"label",title);
    }
  },
});
