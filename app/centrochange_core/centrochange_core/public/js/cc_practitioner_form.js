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
      appointments:"Disponibilità",charges:"Tariffe professionali",free_followup_details_section:"Visite di controllo gratuite",
      address_and_contacts_section:"Indirizzi e contatti", practitioner_name:"Nome e cognome",status:"Stato",
      mobile_phone:"Cellulare", practitioner_type:"Tipo di professionista",user_id:"Utente collegato",
      department:"Reparto",employee:"Dipendente collegato"})) {
      if(frm.fields_dict[field]) frm.set_df_property(field,"label",title);
    }
    if (!frm.doc.department) frm.toggle_display("department", false);
    if (!frm.__ccUxSectionsPrepared) {
      for (const section of frm.layout?.sections || []) {
        if (["charges","free_followup_details_section","account_details","primary_address_and_contact_detail"].includes(section.df.fieldname))
          section.collapse(true);
      }
      frm.__ccUxSectionsPrepared = true;
    }
    const toolsOpen = Boolean(frm.__ccNativeToolsOpen);
    document.body.dataset.ccNativeTools = toolsOpen ? "1" : "0";
    frm.remove_custom_button("Strumenti e tracciabilità");
    frm.remove_custom_button("Chiudi strumenti");
    frm.add_custom_button(toolsOpen ? "Chiudi strumenti" : "Strumenti e tracciabilità", () => {
      frm.__ccNativeToolsOpen = !toolsOpen;
      frm.trigger("refresh");
    });
    frm.page.main.find(".cc-native-help").remove();
    frm.page.main.find(".form-layout").first().before('<section class="cc-native-help" aria-label="Guida alla compilazione"><strong>Come compilare</strong><span>Compila nome, stato e tipo di professionista nei campi nativi. Verifica il collegamento all’utente e i recapiti; i campi con * sono obbligatori. Le tariffe e i dettagli di controllo sono sezioni avanzate. Usa Salva per confermare e correggi gli eventuali campi segnalati.</span></section>');
  },
});
