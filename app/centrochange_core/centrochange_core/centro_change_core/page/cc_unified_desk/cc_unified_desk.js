frappe.pages['cc-unified-desk'].on_page_load = function(wrapper) {
  const page = frappe.ui.make_app_page({parent: wrapper, title: 'Centro Change · Desk sperimentale', single_column: true});
  const root = $('<section class="cc-desk" aria-label="Centro Change Unified Desk"></section>').appendTo(page.main);
  const esc = frappe.utils.escape_html;
  const call = async (method,args={},post=false) => {
    const response=await fetch('/api/method/centrochange_core.'+method+(post?'':'?'+new URLSearchParams(args)), {method:post?'POST':'GET',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':frappe.csrf_token},...(post?{body:JSON.stringify(args)}:{})});
    const result=await response.json();
    if(!response.ok) throw new Error(response.status===403?'Accesso non autorizzato nel contesto selezionato.':'Operazione non riuscita. Verifica dati e autorizzazioni.');
    return result.message;
  };
  const state={view:'Agenda',generation:0,boot:null,finance:null};
  const iso=d=>new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10);
  const today=iso(new Date());
  const date=d=>new Date(d+'T12:00:00').toLocaleDateString('it-IT');
  const money=v=>new Intl.NumberFormat('it-IT',{style:'currency',currency:'EUR'}).format(v||0);
  const human=v=>{const text=String(v||'').replace(/CC-HTTP-[A-Za-z0-9]+\s+/g,'');return ({a:'Alfa',b:'Beta',c:'Gamma'})[text]||text;};
  const label=v=>({'Scheduled':'Prenotata','Open':'Aperta','Closed':'Chiusa','Cancelled':'Cancellata','Paid':'Pagata','Unpaid':'Da pagare','Pending':'In attesa','Overdue':'Scaduta','OK':'Confermato','SUSPENDED':'Sospeso','REVIEW':'Da verificare'})[v]||v||'—';
  const center=page.add_field({fieldname:'center',label:'Centro',fieldtype:'Select',options:[],change:()=>{if(!setting)load();}});
  const start=page.add_field({fieldname:'start',label:'Dal',fieldtype:'Date',default:today,change:()=>{if(!setting)load();}});
  const end=page.add_field({fieldname:'end',label:'Al',fieldtype:'Date',default:today,change:()=>{if(!setting)load();}});
  const nav=$('<nav class="cc-nav" aria-label="Percorsi Centro Change"></nav>').appendTo(root);
  const content=$('<div class="cc-content" aria-live="polite"></div>').appendTo(root);
  const context=()=>({center:center.get_value(),start:start.get_value(),end:end.get_value()});
  const error=e=>{content.empty().append($('<div class="alert alert-danger" role="alert"></div>').text(e.message));};
  function table(rows,columns,click){
    const t=$('<table><thead><tr></tr></thead><tbody></tbody></table>');
    columns.forEach(c=>t.find('thead tr').append($('<th scope="col"></th>').text(c[1])));
    for(const row of rows){const tr=$('<tr></tr>').appendTo(t.find('tbody'));columns.forEach(([key],index)=>{const td=$('<td></td>').appendTo(tr);const text=row[key]??'—';if(index===0&&click)$('<button class="btn btn-link btn-sm"></button>').text(text).on('click',()=>click(row)).appendTo(td);else td.text(text);});}
    if(!rows.length)t.find('tbody').append($('<tr></tr>').append($('<td></td>').attr('colspan',columns.length).text('Nessun risultato autorizzato nel periodo.')));
    return $('<div class="cc-scroll"></div>').append(t);
  }
  function dialog(title,html){const d=new frappe.ui.Dialog({title,fields:[{fieldtype:'HTML',fieldname:'body'}]});d.fields_dict.body.$wrapper.append(html);d.show();return d;}
  async function appointment(row){try{
    const history=await call('operations.workspace.patient_history',{center:context().center,patient:row.patient});
    const found=history.appointments.find(a=>a.name===row.name);if(!found)throw new Error('Seduta non più disponibile nel contesto autorizzato.');
    const box=$('<div></div>').append($('<h5></h5>').text(human(row.patient_name||row.patient)))
      .append($('<p></p>').text(date(row.appointment_date)+' · '+row.appointment_time+' · '+label(row.status)+' · '+label(row.cc_closure_state)));
    box.append($('<h6>Seduta</h6>'),$('<p></p>').text(row.cc_service_label||'Seduta'));
    box.append($('<h6>Storico</h6>'),table(history.appointments.map(a=>({...a,day:date(a.appointment_date),state:label(a.status)})),[['day','Data'],['appointment_time','Ora'],['state','Stato']]));
    box.append($('<h6>Note organizzative</h6>'));history.organizational_notes.forEach(n=>box.append($('<p></p>').text(n.content)));
    if(history.private_notes?.length){box.append($('<h6>Note private del professionista</h6>'));history.private_notes.forEach(n=>box.append($('<p></p>').text(n.content)));}
    const d=dialog('Dettaglio seduta',box);
    // Canonical services remain authoritative; no direct native document mutation.
    const actions=$('<div class="cc-nav"></div>').appendTo(box);
    $('<button class="btn btn-default">Sposta</button>').appendTo(actions).on('click',()=>{const m=new frappe.ui.Dialog({title:'Sposta seduta',fields:[{fieldname:'appointment_date',label:'Data',fieldtype:'Date',reqd:1,default:row.appointment_date},{fieldname:'appointment_time',label:'Ora',fieldtype:'Time',reqd:1,default:row.appointment_time},{fieldname:'reason',label:'Motivo',fieldtype:'Small Text',reqd:1}],primary_action_label:'Conferma',primary_action:async values=>{try{await call('scheduling.booking.reschedule',{appointment:row.name,...values},true);m.hide();d.hide();await load();}catch(e){frappe.msgprint(e.message);}}});m.show();});
    $('<button class="btn btn-default">Cancella seduta</button>').appendTo(actions).on('click',()=>{const m=new frappe.ui.Dialog({title:'Cancella seduta',fields:[{fieldname:'reason',label:'Motivo',fieldtype:'Small Text',reqd:1}],primary_action_label:'Conferma cancellazione',primary_action:async values=>{try{await call('operations.lifecycle.cancel',{appointment:row.name,...values},true);m.hide();d.hide();await load();}catch(e){frappe.msgprint(e.message);}}});m.show();});
    $('<button class="btn btn-default">Apri percorso operativo completo</button>').appendTo(actions).on('click',()=>window.open('/centrochange','_blank','noopener'));
  }catch(e){frappe.msgprint(e.message);}}
  async function book(){
    if(!state.boot)return;
    const boot=await call('operations.workspace.bootstrap',{center:center.get_value()});
    const patientNames=new Map();
    const d=new frappe.ui.Dialog({title:'Prenota seduta',fields:[
      {fieldname:'patient',label:'Paziente',fieldtype:'Autocomplete',options:[],reqd:1},
      {fieldname:'practitioner',label:'Professionista',fieldtype:'Autocomplete',options:boot.practitioners.map(p=>({label:human(p.practitioner_name),value:p.name})),reqd:1},
      {fieldname:'appointment_type',label:'Servizio',fieldtype:'Select',options:boot.services.map(s=>({label:s.service_label||s.name,value:s.name})),reqd:1},
      {fieldname:'appointment_date',label:'Data',fieldtype:'Date',default:start.get_value(),reqd:1},
      {fieldname:'appointment_time',label:'Ora',fieldtype:'Time',reqd:1},
      {fieldname:'reason',label:'Motivo',fieldtype:'Small Text',reqd:1}],primary_action_label:'Prenota',primary_action:async values=>{
        try{await call('scheduling.booking.book',{...values,center:center.get_value(),request_key:key},true);d.hide();await load();}catch(e){frappe.msgprint(e.message);}
      }});
    const key=Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,'0')).join('');
    let generation=0;const control=d.fields_dict.patient;
    control.$input.on('input',async()=>{const g=++generation;const search=control.get_value();try{
      const rows=await call('operations.workspace.patient_search',{center:center.get_value(),query:search});
      if(g!==generation)return;control.set_data(rows.patients.map(p=>({label:human(p.patient_name),value:p.name})));
    }catch(e){if(g===generation)frappe.msgprint(e.message);}});
    d.show();
  }
  async function invoice(row){try{
    const response=await fetch('/api/resource/Sales%20Invoice/'+encodeURIComponent(row.name),{credentials:'same-origin'});if(!response.ok)throw new Error('Documento non autorizzato.');const doc=(await response.json()).data;
    const boot=await call('finance.reporting.bootstrap',{center:context().center});
    const box=$('<div></div>').append($('<p></p>').text(row.name+' · '+date(doc.posting_date)),table([{customer:human(doc.customer),gross:money(doc.grand_total),residue:money(doc.outstanding_amount),due:date(doc.due_date),state:label(doc.status)}],[['customer','Soggetto fiscale'],['gross','Emesso'],['residue','Residuo'],['due','Scadenza'],['state','Stato']]));
    const detail=dialog('Fattura paziente',box);
    if(boot.can_write&&doc.docstatus===1&&doc.outstanding_amount>0)$('<button class="btn btn-primary">Registra incasso</button>').appendTo(box).on('click',()=>{
      const key=Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,'0')).join('');
      const d=new frappe.ui.Dialog({title:'Registra incasso',fields:[{fieldname:'amount',label:'Importo',fieldtype:'Currency',default:doc.outstanding_amount,reqd:1},{fieldname:'posting_date',label:'Data contabile',fieldtype:'Date',default:today,reqd:1},{fieldname:'reason',label:'Motivo',fieldtype:'Small Text',reqd:1}],primary_action_label:'Conferma incasso',primary_action:async values=>{try{await call('finance.receivables.pay',{name:row.name,...values,request_key:key},true);d.hide();detail.hide();await load();}catch(e){frappe.msgprint(e.message);}}});d.show();
    });
  }catch(e){frappe.msgprint(e.message);}}
  async function load(){
    if(!center.get_value())return;const generation=++state.generation;content.text('Caricamento…');
    page.clear_primary_action();
    try{
      const ctx=context();if(state.view==='Agenda'){
        const boot=await call('operations.workspace.bootstrap',{center:ctx.center});
        const data=await call('operations.workspace.agenda',ctx);if(generation!==state.generation)return;state.boot=boot;content.empty();
        const anchor=new Date(ctx.start+'T12:00:00');anchor.setDate(anchor.getDate()-((anchor.getDay()+6)%7));
        const dates=Array.from({length:7},(_,i)=>{const d=new Date(anchor);d.setDate(d.getDate()+i);return iso(d);});
        const bar=$('<div class="cc-nav"></div>').appendTo(content);
        for(const [text,days] of [['‹ Settimana',-7],['Oggi',null],['Settimana ›',7]])$('<button class="btn btn-default"></button>').text(text).appendTo(bar).on('click',()=>{const d=days===null?new Date():new Date(ctx.start+'T12:00:00');if(days!==null)d.setDate(d.getDate()+days);setWeek(d);});
        $('<p class="cc-note"></p>').text(date(dates[0])+' – '+date(dates[6])+' · dati autorizzati, massimo 200 sedute').appendTo(content);
        const grid=$('<div class="cc-week"></div>').appendTo($('<div class="cc-scroll"></div>').appendTo(content));
        const header=$('<div class="cc-tracks cc-header"></div>').appendTo(grid);$('<div class="cc-track cc-day">Professionista</div>').appendTo(header);
        dates.forEach(day=>$('<div class="cc-track cc-day"></div>').attr('data-day',day).text(new Date(day+'T12:00:00').toLocaleDateString('it-IT',{weekday:'short',day:'numeric',month:'short'})).appendTo(header));
        boot.practitioners.forEach(p=>{const line=$('<div class="cc-tracks cc-professional-row"></div>').appendTo(grid);$('<div class="cc-track cc-row-name"></div>').text(human(p.practitioner_name)).appendTo(line);dates.forEach(day=>{const cell=$('<div class="cc-track cc-cell"></div>').attr('data-day',day).appendTo(line);data.appointments.filter(a=>a.practitioner===p.name&&a.appointment_date===day).forEach(a=>$('<button class="cc-event"></button>').attr('data-appointment',a.name).text(a.appointment_time.slice(0,5)+' · '+human(a.patient_name)+' · '+label(a.status)).appendTo(cell).on('click',()=>appointment(a)));});});
        if(data.truncated)content.append('<p class="alert alert-warning">Risultati limitati: restringi il periodo.</p>');
        page.set_primary_action('Prenota',()=>book().catch(e=>frappe.msgprint(e.message)));
      }else if(state.view==='Pazienti'){
        const boot=await call('operations.workspace.bootstrap',{center:ctx.center});if(generation!==state.generation)return;content.empty().append(table(boot.patients.map(p=>({...p,display:human(p.patient_name)})),[['display','Paziente'],['name','Riferimento']],async p=>{try{const h=await call('operations.workspace.patient_history',{center:ctx.center,patient:p.name});dialog('Storico · '+human(p.patient_name),table(h.appointments,[['appointment_date','Data'],['appointment_time','Ora'],['cc_service_label','Servizio'],['status','Stato']],appointment));}catch(e){frappe.msgprint(e.message);}}));
        $('<button class="btn btn-default">Elenco nativo autorizzato</button>').appendTo(content).on('click',()=>frappe.set_route('List','Patient'));
      }else if(state.view==='Finance'){
        const data=await call('finance.reporting.summary',ctx);if(generation!==state.generation)return;content.empty();const k=$('<div class="cc-kpis"></div>').appendTo(content);
        for(const [key,title] of [['billed_gross','Fatturato'],['collected','Incassato'],['receivable_outstanding','Residuo']])$('<div class="cc-kpi"></div>').append($('<strong></strong>').text(title),$('<p></p>').text(money(data.totals[key]))).appendTo(k);
        content.append($('<p class="cc-note"></p>').text('Fatture e incassi: data contabile. Sedute: data seduta. Nessuna ripartizione del saldo tra pazienti con soggetto fiscale condiviso.'));
        content.append(table(data.sales_invoices.map(i=>({...i,amount:money(i.grand_total),residue:money(i.outstanding_amount)})),[['name','Fattura'],['posting_date','Data contabile'],['amount','Emesso'],['residue','Residuo']],invoice));
        $('<button class="btn btn-default">Percorso Finance completo</button>').appendTo(content).on('click',()=>window.open('/finanza','_blank','noopener'));
      }
    }catch(e){if(generation===state.generation)error(e);}
  }
  let setting=false;
  function setWeek(d){const a=new Date(d);a.setDate(a.getDate()-((a.getDay()+6)%7));const b=new Date(a);b.setDate(b.getDate()+6);setting=true;start.set_value(iso(a));end.set_value(iso(b));setting=false;load();}
  async function init(){
    const roles=frappe.user_roles||[];const operations=roles.some(r=>['CC Manager','CC Secretariat','CC Professional'].includes(r));const finance=roles.some(r=>['CC Manager','CC Secretariat','CC Finance','CC Accountant'].includes(r));
    const views=[...(operations?['Agenda','Pazienti']:[]),...(finance?['Finance']:[])];
    if(!views.length){error(new Error('Accesso non autorizzato.'));return;}
    state.view=views[0];views.forEach(view=>$('<button class="btn btn-default"></button>').text(view).attr('data-view',view).appendTo(nav).on('click',()=>{state.view=view;load();}));
    const boot=await call(operations?'operations.workspace.bootstrap':'finance.reporting.bootstrap');
    center.df.options=boot.centers.map(c=>({label:human(c.branch||c.name),value:c.name}));center.refresh();await center.set_value(boot.center||boot.centers[0]?.name||'');setWeek(new Date());
  }
  $(wrapper).on('hide',()=>{state.generation++;});
  init().catch(error);
};
