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
  const apply=(doctype,title,fields,options={})=>{
    const prior=frappe.listview_settings[doctype]||{};
    const formatters={...prior.formatters};
    for(const [field,fn] of Object.entries(fields)) formatters[field]=value=>esc(fn(value));
    frappe.listview_settings[doctype]={...prior,...options,formatters,onload(listview){
      prior.onload?.call(this,listview);
      listview.page.set_title(title);
    }};
  };
  apply("Item","Catalogo servizi",{item_name:service,item_code:service},{hide_name_column:true,hide_name_filter:true});
  apply("Item Price","Tariffe",{
    item_name:service,item_code:service,
    price_list:value=>({"Standard Selling":"Listino vendite standard","Standard Buying":"Listino acquisti standard"})[value]||(/^CC-HTTP-UAT\d+\s+PRICE$/.test(value)?"Listino Centro Change":value)
  });
  apply("Sales Invoice","Fatture pazienti",{customer:patient,customer_name:patient});
  apply("Purchase Invoice","Fatture professionisti",{supplier:professional,supplier_name:professional});
  apply("Bank Transaction","Movimenti bancari",{
    bank_account:bank,
    description:value=>String(value??"").replace(/^SYNTHETIC UAT\s+/i,"")
  });
  apply("Payment Entry","Incassi e pagamenti",{party:demo});
})();
