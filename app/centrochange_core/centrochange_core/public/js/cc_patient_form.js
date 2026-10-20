/* Supported native Form Script: human title, canonical fields unchanged. */
frappe.ui.form.on("Patient", {
  refresh(frm) {
    if (frappe.session.user === "Administrator" || !(frappe.user_roles || []).some(role => role.startsWith("CC "))) return;
    // Pinned Frappe v16 caches the server-translated dashboard by DocType,
    // rather than by user language. Localize only this client-facing message
    // after the native dashboard has rendered; retain its native heatmap.
    if (frm.dashboard?.data?.heatmap) {
      const message=__("This is based on transactions against this Patient. See timeline below for details");
      frm.dashboard.data.heatmap_message=message;
      frm.dashboard.heatmap_area?.body?.find(".heatmap-message").text(message);
    }
    const label=String(frm.doc.patient_name||"").replace(/^CC-HTTP-UAT\d+\s+/,"");
    if(label) frm.page.set_title(label);
    for(const [field,title] of Object.entries({basic_info:"Dati anagrafici",customer_details_section:"Dati amministrativi",
      more_info:"Informazioni avanzate",address_and_contact_tab:"Indirizzi e contatti",address_contacts:"Recapiti",
      medical_history_tab:"Dati clinici riservati",allergy_medical_and_surgical_history:"Allergie e storia clinica",
      personal_and_social_history:"Storia personale e sociale",risk_factors:"Fattori di rischio",
      patient_name:"Nome e cognome",sex:"Sesso",dob:"Data di nascita",uid:"Identificativo paziente",
      mobile:"Cellulare",email:"Email",status:"Stato",customer:"Soggetto fiscale"})) {
      if(frm.fields_dict[field]) frm.set_df_property(field,"label",title);
    }
    for (const tab of frm.layout?.tabs || []) {
      const label = {address_and_contact_tab:"Indirizzi e contatti",medical_history_tab:"Dati clinici riservati"}[tab.df.fieldname];
      if (label) { tab.df.label = label; tab.refresh(); }
    }
    if (!frm.__ccUxSectionsPrepared) {
      for (const section of frm.layout?.sections || []) {
        if (["more_info","allergy_medical_and_surgical_history","personal_and_social_history","risk_factors"].includes(section.df.fieldname))
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
    // Guidance sits alongside editable native controls; it does not replace
    // DocFields, validation, clinical permissions or the normal Save action.
    frm.page.main.find(".cc-native-help").remove();
    frm.page.main.find(".form-layout").first().before('<section class="cc-native-help" aria-label="Guida alla compilazione"><strong>Come compilare</strong><span>Inserisci i dati anagrafici e i recapiti nei campi qui sotto. I campi contrassegnati con * sono obbligatori; gli altri sono facoltativi. I dati clinici riservati si trovano nella scheda dedicata e restano accessibili solo ai ruoli autorizzati. Usa Salva per confermare; in caso di errore correggi il campo indicato.</span></section>');
  },
});
