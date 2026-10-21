/* Native List View presentation, limited to Centro Change users. All native
   actions, data and server permissions remain authoritative. */
(() => {
  if (frappe.session.user === "Administrator" || !(frappe.user_roles || []).some(role => role.startsWith("CC "))) return;
  const esc = value => frappe.utils.escape_html(String(value ?? ""));
  const demo = value => String(value ?? "").replace(/^CC-HTTP-UAT\d+\s+/, "");
  // Retained, canceled accounting fixtures keep their canonical customer and
  // document IDs. Give the client list a readable subject; the document ID
  // remains visible in its native column and the full form/audit is intact.
  const patient = value => /^CC-MVP-POS-[\w-]+$/.test(String(value ?? ""))
    ? "Paziente dimostrativo POS" : demo(value);
  const service = value => {
    const label=demo(value);
    return label.toLowerCase()==="session" ? "Seduta" : label;
  };
  const professional = value => {
    const label=demo(value);
    return ({a:"Professionista Alfa",b:"Professionista Beta",c:"Professionista Gamma"})[label]||label;
  };
  const bank = value => {
    const original=String(value ?? "");
    const match=original.match(/^CC DEV CC-HTTP-UAT\d+\s+([A-Z])(?: - CC SYNTHETIC BANK)?$/);
    return match ? `Conto Centro ${match[1]}` : original;
  };
  // Frappe v16 List View uses the canonical raw value in its native tooltip.
  // A scoped formatter keeps the exact filter value while showing an Italian
  // date both in the row and the tooltip. API/DB values remain ISO.
  const dateColumn = (field,label) => value => {
    const raw=String(value??"");
    if(!/^\d{4}-\d{2}-\d{2}$/.test(raw))return esc(raw);
    const shown=`${raw.slice(8,10)}/${raw.slice(5,7)}/${raw.slice(0,4)}`;
    return `<span title="${label}: ${shown}"><a class="filterable ellipsis" data-filter="${field},=,${raw}">${shown}</a></span>`;
  };
  const localizeCatalogFilterTitle = listview => {
    // Pinned Frappe 16.50 constructs this one tooltip as an English literal,
    // bypassing __(). Observe only the native Catalog filter button; leave
    // its button, filters and List View behavior under Frappe control.
    const button=listview.filter_area?.filter_button?.[0];
    if(!button || button.__ccItalianFilterTitle)return;
    const update=()=>{
      const current=button.getAttribute('title')||'';
      const count=current.match(/^(\d+) Filters? Applied$/);
      if(count)button.setAttribute('title',`${count[1]} ${Number(count[1])===1?'filtro applicato':'filtri applicati'}`);
    };
    const observer=new MutationObserver(update);
    observer.observe(button,{attributes:true,attributeFilter:['title']});
    button.__ccItalianFilterTitle=observer;
    update();
  };
  const apply=(doctype,title,fields,options={})=>{
    const prior=frappe.listview_settings[doctype]||{};
    const formatters={...prior.formatters};
    for(const [field,fn] of Object.entries(fields)) formatters[field]=value=>esc(fn(value));
    for(const [field,fn] of Object.entries(options.rawFormatters||{}))formatters[field]=fn;
    const {rawFormatters,...viewOptions}=options;
    frappe.listview_settings[doctype]={...prior,...viewOptions,formatters,onload(listview){
      prior.onload?.call(this,listview);
      // Frappe 16.50 builds the subject header after onload, but its sort
      // tooltip interpolates the unlocalized DocField label. Adjust only the
      // client List column; its fieldname, filter and stored value stay native.
      const subject=listview.columns?.[0]?.df;
      const subjectNames={"Customer Name":"Paziente","Supplier Name":"Professionista",
        "Item Name":"Servizio"};
      if(subjectNames[subject?.label])subject.label=subjectNames[subject.label];
      if(doctype==="Item")localizeCatalogFilterTitle(listview);
      listview.page.set_title(title);
    }};
  };
  apply("Item","Catalogo servizi",{item_name:service,item_code:service},{hide_name_column:true,hide_name_filter:true});
  apply("Item Price","Tariffe",{
    item_name:service,item_code:service,
    price_list:value=>({"Standard Selling":"Listino vendite standard","Standard Buying":"Listino acquisti standard"})[value]||(/^CC-HTTP-UAT\d+\s+PRICE$/.test(value)?"Listino Centro Change":value)
  });
  apply("Appointment Type","Tipi di seduta",{}, {rawFormatters:{allow_booking_for:value=>{
    const raw=String(value??"");
    const shown=__(raw);
    return `<span class="ellipsis" title="${esc(__("Allow Booking For"))}: ${esc(shown)}"><span class="es-badge filterable ellipsis" data-filter="allow_booking_for,=,${esc(raw)}"><span class="es-badge__label">${esc(shown)}</span></span></span>`;
  }}});
  apply("Sales Invoice","Fatture pazienti",{customer:patient,customer_name:patient},{
    rawFormatters:{posting_date:dateColumn("posting_date","Data contabile"),
      due_date:dateColumn("due_date","Scadenza pagamento")}});
  apply("Purchase Invoice","Fatture professionisti",{supplier:professional,supplier_name:professional},{
    rawFormatters:{posting_date:dateColumn("posting_date","Data contabile"),
      due_date:dateColumn("due_date","Scadenza pagamento")}});
  apply("Bank Transaction","Movimenti bancari",{
    bank_account:bank,
    description:value=>String(value??"").replace(/^SYNTHETIC UAT\s+/i,"")
  });
  apply("Payment Entry","Incassi e pagamenti",{party:demo},{
    rawFormatters:{posting_date:dateColumn("posting_date","Data contabile")}});
})();
