/* Native accounting form context. Native DocPerm and server guards decide access. */
(() => {
  if (window.__ccFinanceFormsRegistered) return;
  window.__ccFinanceFormsRegistered = true;
  const roles = () => new Set(frappe.user_roles || []);
  const client = () => frappe.session.user !== "Administrator" &&
    ["CC Manager","CC Secretariat","CC Finance","CC Accountant"].some(r => roles().has(r));
  const canWrite = () => ["CC Manager","CC Secretariat","CC Finance"].some(r => roles().has(r));
  const simple = () => ["CC Manager","CC Secretariat"].some(r => roles().has(r)) &&
    !roles().has("CC Finance") && !roles().has("CC Accountant");
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const money = (value,currency) => new Intl.NumberFormat("it-IT",{style:"currency",currency:currency||"EUR"}).format(Number(value)||0);
  const date = value => value ? new Intl.DateTimeFormat("it-IT").format(new Date(value+"T12:00:00")) : "Non indicata";
  function state(d) {
    if (d.docstatus===2) return "Annullato";
    if (d.docstatus===0) return "Bozza";
    if (d.outstanding_amount!=null && Number(d.outstanding_amount)<=0) return "Saldato";
    if (d.outstanding_amount!=null && Number(d.outstanding_amount)<Number(d.grand_total||0)) return "Parzialmente saldato";
    return "Contabilizzato";
  }
  function summary(frm,heading,facts,next,guide) {
    const rows=facts.filter(([,v])=>v!==undefined&&v!==null&&v!=="")
      .map(([label,value])=>'<div><dt>'+esc(label)+'</dt><dd>'+esc(value)+'</dd></div>').join("");
    // Form dashboard sections sit below the fields in pinned Frappe v16.
    // Place this presentation block before the existing native form layout.
    frm.page.main.find(".cc-finance-context").remove();
    frm.page.main.find(".form-layout").first().before('<section class="cc-finance-context" aria-label="Guida al documento"><div><h2>'+esc(heading)+'</h2><dl>'+rows+'</dl></div><p><strong>Come procedere</strong><span>'+esc(next)+'</span>'+(guide?'<strong>Come compilare</strong><span>'+esc(guide)+'</span>':'')+'</p></section>');
  }
  function advanced(frm,fields) {
    if (!simple()) return;
    const show=Boolean(frm.__ccFinanceAdvanced);
    for (const field of fields) if (frm.fields_dict[field] && !frm.fields_dict[field].df.reqd) frm.toggle_display(field,show);
    if(frm.doctype==="Sales Invoice" && frm.fields_dict.items?.grid){
      frm.fields_dict.items.grid.update_docfield_property("warehouse","in_list_view",show?1:0);
      frm.fields_dict.items.grid.refresh();
    }
    frm.remove_custom_button("Dettagli contabili");
    frm.remove_custom_button("Riduci dettagli");
    frm.add_custom_button(show?"Riduci dettagli":"Dettagli contabili",()=>{
      frm.__ccFinanceAdvanced=!show;frm.trigger("refresh");
    });
    if(frm.doctype==="Sales Invoice")frm.page.get_inner_group_button(__("Get Items From")).toggle(show);
    document.body.dataset.ccFinanceAdvanced=show?"1":"0";
  }
  const invoiceNext = frm => {
    const d=frm.doc;
    if (d.docstatus===2) return "Documento annullato. Consulta la cronologia; eventuali rettifiche seguono il flusso autorizzato.";
    if (d.docstatus===0) return canWrite()
      ? "Controlla soggetto, prestazioni, imposte e totale; apri Finanza per contabilizzare con il flusso autorizzato."
      : "Controlla la bozza. La contabilizzazione richiede un operatore autorizzato.";
    if (Number(d.outstanding_amount||0)<=0) return "Documento saldato. Consulta pagamenti e riferimenti.";
    return canWrite() ? "Verifica residuo e scadenza; registra il pagamento dalla funzione Finanza se previsto dal flusso autorizzato."
      : "Consulta residuo e pagamenti. La registrazione è riservata agli operatori autorizzati.";
  };
  const invoiceAdvanced=["accounting_dimensions_section","taxes_section","section_tax_withholding_entry","sec_tax_breakup","terms_tab","more_info_tab","connections_tab","update_stock"];
  frappe.ui.form.on("Sales Invoice",{refresh(frm){
    if(!client())return;
    frm.page.set_title(frm.is_new()?"Nuova":"Dettaglio");
    for(const [field,label] of Object.entries({customer_section:"Paziente e documento",items_section:"Prestazioni",payments_tab:"Pagamenti",
      customer:"Paziente o soggetto fiscale",posting_date:"Data documento",due_date:"Scadenza",grand_total:"Totale",
      outstanding_amount:"Residuo da incassare",items:"Prestazioni fatturate",taxes:"Imposte",total_taxes_and_charges:"Totale imposte"}))
      if(frm.fields_dict[field])frm.set_df_property(field,"label",label);
    const d=frm.doc;
    summary(frm,"Fattura paziente",[["Documento",d.name||"Nuova fattura"],["Paziente",d.patient_name||d.customer_name||d.customer],
      ["Stato",state(d)],["Totale",money(d.grand_total,d.currency)],
      ["Pagato",d.docstatus===1&&d.outstanding_amount!=null?money(Math.max(0,Number(d.grand_total||0)-Number(d.outstanding_amount)),d.currency):undefined],
      ["Residuo",d.docstatus===1&&d.outstanding_amount!=null?money(d.outstanding_amount,d.currency):undefined],
      ["Scadenza",date(d.due_date)],["Prestazioni",(d.items||[]).map(r=>r.item_name||r.item_code).filter(Boolean).join(", ")]],
      invoiceNext(frm),"Seleziona il paziente e inserisci le prestazioni nei campi qui sotto. I campi con * sono obbligatori; verifica data, imposte e totale prima di usare Salva. I dettagli contabili restano disponibili ai ruoli autorizzati.");
    advanced(frm,[...invoiceAdvanced,"additional_discount_section","contact_and_address_tab","cc_fiscal_profile","company_tax_id","posting_time","set_posting_time","is_pos",
      ...(d.is_return?[]:["is_return"]),...(d.is_debit_note?[]:["is_debit_note"]),"apply_tds","update_outstanding_for_self"]);
  }});
  frappe.ui.form.on("Purchase Invoice",{refresh(frm){
    if(!client())return;
    frm.page.set_title(frm.is_new()?"Nuova":"Dettaglio");
    for(const [field,label] of Object.entries({supplier_invoice_details:"Documento del professionista",payments_tab:"Pagamenti",
      supplier:"Professionista o fornitore",bill_no:"Numero documento ricevuto",bill_date:"Data documento ricevuto",
      posting_date:"Data registrazione",due_date:"Scadenza",items:"Prestazioni e voci",grand_total:"Totale",
      outstanding_amount:"Residuo da pagare",taxes:"Imposte"}))
      if(frm.fields_dict[field])frm.set_df_property(field,"label",label);
    const d=frm.doc;
    summary(frm,"Fattura professionista",[["Documento",d.bill_no||d.name||"Nuova fattura"],["Professionista",d.supplier_name||d.supplier],
      ["Data",date(d.posting_date)],["Stato",state(d)],["Totale",money(d.grand_total,d.currency)],["Residuo",money(d.outstanding_amount,d.currency)]],
      invoiceNext(frm),"Seleziona il professionista o fornitore, inserisci il numero ricevuto e le voci. I campi con * sono obbligatori. Verifica importi e imposte, poi usa Salva; correggi gli eventuali campi segnalati.");
    advanced(frm,[...invoiceAdvanced,"address_and_contact_tab","cc_fiscal_profile","company_tax_id","posting_time","set_posting_time","update_outstanding_for_self"]);
  }});
  frappe.ui.form.on("Payment Entry",{refresh(frm){
    if(!client())return;
    frm.page.set_title(frm.is_new()?"Nuovo":"Dettaglio");
    for(const [field,label] of Object.entries({type_of_payment:"Operazione",party_section:"Soggetto",payment_accounts_section:"Conti",payment_amounts_section:"Importi",transaction_references:"Riferimenti",
      payment_type:"Tipo di operazione",party:"Soggetto",mode_of_payment:"Metodo di pagamento",posting_date:"Data",
      references:"Documenti collegati",paid_amount:"Importo pagato",received_amount:"Importo incassato",
      unallocated_amount:"Da allocare"}))
      if(frm.fields_dict[field])frm.set_df_property(field,"label",label);
    const d=frm.doc,kind=d.payment_type==="Receive"?"Incasso":d.payment_type==="Pay"?"Pagamento":"Trasferimento";
    const next=d.docstatus===2?"Operazione annullata: consulta riferimenti e cronologia.":d.docstatus===0?
      (canWrite()?"Verifica soggetto, documento, importo e conti; usa il flusso Finanza autorizzato per contabilizzare.":"Consulta la bozza; un operatore autorizzato può completarla."):
      "Operazione contabilizzata: verifica documento collegato e importo allocato.";
    summary(frm,kind,[["Documento",d.name||"Nuova operazione"],["Soggetto",d.party_name||d.party],["Stato",d.docstatus===2?"Annullata":d.docstatus===1?"Contabilizzata":"Bozza"],
      ["Importo",money(d.payment_type==="Receive"?d.received_amount:d.paid_amount,d.paid_to_account_currency||d.paid_from_account_currency)],
      ["Documento collegato",(d.references||[]).map(r=>r.reference_name).filter(Boolean).join(", ")||"Da collegare"],
      ["Da allocare",money(d.unallocated_amount,d.paid_to_account_currency||d.paid_from_account_currency)],["Data",date(d.posting_date)]],next,
      "Seleziona il tipo di operazione, il soggetto, il metodo e il documento da saldare. I campi con * sono obbligatori. Verifica importo e conto prima di usare Salva.");
    advanced(frm,["accounting_dimensions_section","taxes_and_charges_section","deductions_or_loss_section","section_tax_withholding_entry","auto_repeat_section"]);
  }});
  frappe.ui.form.on("Bank Transaction",{refresh(frm){
    if(!client())return;
    frm.page.set_title(frm.is_new()?"Nuovo":"Dettaglio");
    for(const [field,label] of Object.entries({date:"Data movimento",bank_account:"Conto bancario",deposit:"Entrata",
      withdrawal:"Uscita",unallocated_amount:"Da riconciliare",payment_entries:"Documenti collegati"}))
      if(frm.fields_dict[field])frm.set_df_property(field,"label",label);
    const d=frm.doc,credit=Number(d.deposit||0)>0;
    summary(frm,"Movimento bancario",[["Documento",d.name||"Nuovo movimento"],["Direzione",credit?"Entrata":"Uscita"],["Data",date(d.date)],
      ["Importo",money(credit?d.deposit:d.withdrawal,d.currency)],["Conto",d.bank_account],["Da riconciliare",money(d.unallocated_amount,d.currency)]],
      d.docstatus===2?"Movimento annullato: consulta riferimenti e cronologia.":Number(d.unallocated_amount||0)>0?
        (canWrite()?"Verifica il documento corrispondente e completa l’abbinamento dalla funzione Banca quando disponibile.":"Movimento da riconciliare; consulta i documenti collegati."):
        "Movimento riconciliato: verifica il riferimento al documento e la cronologia.",
      "Verifica data, conto e importo nei campi nativi. Collega un documento solo attraverso la funzione Banca autorizzata; i campi con * sono obbligatori.");
    const technical=Boolean(frm.__ccTechnicalOpen);
    frm.toggle_display(["cc_source_hash","cc_source_key"],technical);
    frm.remove_custom_button("Riferimenti tecnici");
    frm.remove_custom_button("Nascondi riferimenti tecnici");
    frm.add_custom_button(technical?"Nascondi riferimenti tecnici":"Riferimenti tecnici",()=>{frm.__ccTechnicalOpen=!technical;frm.trigger("refresh");});
  }});
})();
