/* Native Healthcare form remains authoritative. These empty optional
   upstream fields are not part of the Centro Change client workflow. */
frappe.ui.form.on("Healthcare Practitioner", {
  refresh(frm) {
    const roles = new Set(frappe.user_roles || []);
    if (!roles.has("CC Manager") || frappe.session.user === "Administrator") return;
    const readable=String(frm.doc.practitioner_name||"").replace(/^CC-HTTP-UAT\d+\s+/,"");
    const label=({a:"Professionista Alfa",b:"Professionista Beta",c:"Professionista Gamma"})[readable]||readable;
    if(label) frm.page.set_title(label);
    for(const [field,title] of Object.entries({basic_details_section:"Dati principali",employee_and_user_details_section:"Collegamenti professionali",
      appointments:"Disponibilità",charges:"Tariffe professionali",address_and_contacts_section:"Recapiti",
      practitioner_name:"Nome e cognome",status:"Stato",mobile_phone:"Cellulare"})) {
      if(frm.fields_dict[field]) frm.set_df_property(field,"label",title);
    }
    if (!frm.doc.department) frm.toggle_display("department", false);
  },
});
