/* Preserve native Item Price validation and commercial rules. */
(() => {
  frappe.ui.form.on("Item Price", {
    refresh(frm) {
      if (frappe.session.user === "Administrator" || !(frappe.user_roles || []).includes("CC Manager")) return;
      const service = String(frm.doc.item_name || frm.doc.item_code || "").replace(/^CC-HTTP-UAT\d+\s+/, "").replace(/^Session$/i, "Seduta");
      if (service) frm.page.set_title(`Tariffa · ${service}`);
      for (const [field, label] of Object.entries({item_code:"Servizio",price_list:"Listino",
        price_list_rate:"Prezzo",currency:"Valuta",valid_from:"Valida dal",valid_upto:"Valida fino al",
        price_list_details:"Listino e prezzo",item_details:"Servizio"})) {
        if (frm.fields_dict[field]) frm.set_df_property(field, "label", label);
      }
      const technical=Boolean(frm.__ccTechnicalOpen);
      document.body.dataset.ccTechnical=technical ? "1" : "0";
      frm.toggle_display(["packing_unit","batch_no","customer","supplier","item_name"],technical);
      frm.page.main.find(".cc-native-help").remove();
      frm.page.main.find(".form-layout").first().before('<section class="cc-native-help" aria-label="Guida alla compilazione"><strong>Come compilare</strong><span>Seleziona servizio e listino, poi inserisci prezzo e valuta nei campi nativi. Aggiungi le date di validità quando previste. I campi con * sono obbligatori; usa Salva per confermare.</span></section>');
      frm.remove_custom_button("Dettagli tecnici");
      frm.remove_custom_button("Vista operativa");
      frm.add_custom_button(technical ? "Vista operativa" : "Dettagli tecnici",()=>{
        frm.__ccTechnicalOpen=!technical;
        frm.trigger("refresh");
      });
    },
  });
})();
