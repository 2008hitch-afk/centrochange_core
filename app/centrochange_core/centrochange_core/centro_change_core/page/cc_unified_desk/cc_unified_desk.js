/* Unified Desk host: native document routes plus custom CC workflows where
 * native forms cannot preserve scheduling, scoped reports or accounting rules.
 * Presentation fragments are generated at build time from shared templates.
 */
frappe.pages['cc-unified-desk'].on_page_load = function(wrapper) {
  const page=frappe.ui.make_app_page({parent:wrapper,title:'Centro Change',single_column:true,hide_sidebar:false});
  const root=$('<div class="cc-client" aria-label="Centro Change"></div>').appendTo(page.main)[0];
  const surfaces={
    agenda:{path:'/centrochange',script:'workspace.js',css:['workspace.css']},
    finance:{path:'/finanza',script:'finance_workspace.js',css:['workspace.css']},
    professional:{path:'/professionista',script:'professional_view.js',css:['workspace.css','professional_view.css']},
    patient:{path:'/pazienti_report',script:'patient_report.js',css:['workspace.css','professional_view.css','patient_report.css']},
    audit:{path:'/registro_modifiche',script:'audit_view.js',css:['workspace.css']}
  };
  const routeByPath=Object.fromEntries(Object.entries(surfaces).map(([name,s])=>[s.path,name]));
  const roles=new Set(frappe.user_roles||[]);
  const canOperate=['CC Manager','CC Secretariat','CC Professional'].some(x=>roles.has(x));
  const canFinance=['CC Manager','CC Secretariat','CC Finance','CC Accountant'].some(x=>roles.has(x));
  const canManage=roles.has('CC Manager');
  const allowed={home:true,agenda:canOperate,finance:canFinance,professional:canFinance,patient:canFinance,audit:canManage};
  const items=[['home','Inizio'],['agenda','Agenda'],['finance','Finanza'],['professional','Report professionisti'],['patient','Report economico pazienti'],['audit','Registro modifiche']];
  const homeByRole=canManage?{
    heading:'Panoramica del Centro',intro:'Le attività quotidiane e i dati economici aggiornati sono nelle rispettive sezioni.',
    links:[{view:'agenda',label:'Apri Agenda',description:'Sedute e prenotazioni'}, {view:'finance',label:'Apri Finanza',description:'Contabilità e posizioni'}, {view:'professional',label:'Report professionisti',description:'Sedute e compensi per periodo'}]
  }:roles.has('CC Professional')?{
    heading:'Il tuo lavoro',intro:'Consulta le sedute e i pazienti che ti sono assegnati.',
    links:[{view:'agenda',label:'Apri Agenda',description:'Sedute e appuntamenti'}, {view:'agenda',params:{cc_ops_view:'Pazienti'},label:'Cerca pazienti',description:'Solo le persone assegnate'}, {view:'agenda',params:{cc_ops_view:'Disponibilità'},label:'Disponibilità',description:'Orari e assenze'}]
  }:roles.has('CC Secretariat')?{
    heading:'Attività di segreteria',intro:'Organizza sedute, pazienti e avvisi del Centro.',
    links:[{view:'agenda',label:'Apri Agenda',description:'Prenotazioni e sedute'}, {view:'agenda',params:{cc_ops_view:'Pazienti'},label:'Cerca pazienti',description:'Schede autorizzate'}, {view:'agenda',params:{cc_ops_view:'Notifiche'},label:'Notifiche',description:'Avvisi operativi'}]
  }:roles.has('CC Accountant')?{
    heading:'Consultazione contabile',intro:'Documenti e report dei centri autorizzati in sola lettura.',
    links:[{view:'finance',label:'Apri Finanza',description:'Posizioni economiche'}, {view:'patient',label:'Report economico pazienti',description:'Saldi e scadenze'}, {href:'/app/sales-invoice',label:'Fatture pazienti',description:'Documenti contabili'}]
  }:{
    heading:'Amministrazione e finanza',intro:'Consulta fatture, incassi e movimenti dei centri autorizzati.',
    links:[{view:'finance',label:'Apri Finanza',description:'Posizioni economiche'}, {href:'/app/sales-invoice',label:'Fatture pazienti',description:'Documenti contabili'}, {view:'finance',params:{cc_fin_view:'Banca'},label:'Banca',description:'Movimenti e riconciliazioni'}]
  };
  function homeContent(){
    const cards=homeByRole.links.map(link=>{
      const href=link.view?routeUrl(link.view,link.params):link.href;
      return `<a class="cc-desk-home-action" href="${href}"><strong>${link.label}</strong><span>${link.description}</span><span aria-hidden="true">›</span></a>`;
    }).join('');
    return `<div class="cc-desk-home"><header class="cc-desk-home-heading"><h1>${homeByRole.heading}</h1><p>${homeByRole.intro}</p></header><section class="cc-desk-home-group" aria-label="Accessi rapidi"><h2>Attività frequenti</h2><div class="cc-desk-home-grid">${cards}</div></section>${canOperate?'<section class="cc-desk-home-summary" aria-label="Dati operativi" aria-live="polite">Caricamento dati operativi…</section>':''}</div>`;
  }
  async function loadHomeSummary(section){
    const target=section.querySelector('.cc-desk-home-summary');
    if(!target)return;
    try{
      const request=async(method,params={})=>{
        const url=new URL('/api/method/centrochange_core.operations.workspace.'+method,location.origin);
        Object.entries(params).forEach(([key,value])=>url.searchParams.set(key,value));
        const response=await fetch(url,{credentials:'same-origin'});
        if(!response.ok)throw new Error('Dati non disponibili');
        return (await response.json()).message;
      };
      const initial=await request('bootstrap');
      const centers=initial.centers||[];
      const today=new Date(),end=new Date(today);
      end.setDate(today.getDate()+6);
      const iso=date=>`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
      const data=await Promise.all(centers.map(center=>Promise.all([
        center.name===initial.center?initial:request('bootstrap',{center:center.name}),
        request('agenda',{center:center.name,start:iso(today),end:iso(end)})
      ])));
      if(!section.isConnected)return;
      const patients=new Set(data.flatMap(([boot])=>boot.patients.map(row=>row.name)));
      const appointments=data.reduce((count,[,agenda])=>count+agenda.appointments.length,0);
      const values=[['Centri accessibili',centers.length],['Pazienti visibili',patients.size],['Sedute nei prossimi 7 giorni',appointments]];
      target.innerHTML=values.map(([label,value])=>`<div><strong>${value}</strong><span>${label}</span></div>`).join('');
    }catch(_){if(section.isConnected)target.textContent='Consulta Agenda e Pazienti per i dati aggiornati.';}
  }
  let generation=0;
  let fragments;
  if(!document.querySelector('meta[name="csrf-token"]')){
    const meta=document.createElement('meta');meta.name='csrf-token';meta.content=frappe.csrf_token;document.head.append(meta);
  }
  async function css(name){
    const id='cc-desk-scoped-'+name.replace(/[^a-z0-9]/gi,'-');if(document.getElementById(id))return;
    const response=await fetch('/assets/centrochange_core/css/'+name,{credentials:'same-origin'});
    if(!response.ok)throw new Error('Asset di presentazione non disponibile: '+name);
    const style=document.createElement('style');style.id=id;style.textContent=await response.text();document.head.append(style);
    // CSSOM scopes the *existing* client stylesheet. Frappe Desk chrome remains native.
    const visit=rules=>{for(const rule of rules){
      if(rule.type===CSSRule.STYLE_RULE){
        rule.selectorText=rule.selectorText.split(',').map(raw=>{
          const s=raw.trim();if(s===':root'||s==='html'||s==='body')return '.cc-client';
          if(s.startsWith('body.'))return '.cc-client '+s.slice(4);
          if(s.startsWith('html.'))return '.cc-client '+s.slice(4);
          return '.cc-client '+s;
        }).join(', ');
      }else if(rule.cssRules&&!/keyframes/i.test(rule.constructor.name))visit(rule.cssRules);
    }};visit(style.sheet.cssRules);
  }
  function routeUrl(view,params){const u=new URL('/app/cc-unified-desk',location.origin);u.searchParams.set('cc_view',view);new URLSearchParams(params||'').forEach((v,k)=>{if(k!=='cc_view')u.searchParams.set(k,v)});return u.pathname+u.search;}
  async function navigate(path,replace=true){
    const u=new URL(path,location.origin),view=u.pathname==='/app/cc-unified-desk'?u.searchParams.get('cc_view')||'home':routeByPath[u.pathname];
    if(!view){if(u.pathname.startsWith('/login'))location.href=u.href;return;}
    if(!Object.hasOwn(allowed,view)||!allowed[view]){root.textContent='Accesso non autorizzato.';return;}
    const token=++generation;root.textContent='Caricamento…';
    if(replace)history.replaceState(null,'',routeUrl(view,u.search));
    try{
      const surface=surfaces[view];
      let fragment;
      if(surface){
        fragments ||= import('/assets/centrochange_core/js/cc_desk_fragments.js');
        const module=await fragments;
        fragment=module.deskFragments[view];
        if(!fragment)throw new Error('Vista Centro Change non disponibile.');
        for(const file of surface.css)await css(file);
      }
      if(token!==generation)return;
      if(view!=='agenda')document.body.classList.remove('is-agenda');
      const section=document.createElement('section');section.className='cc-desk-surface '+(fragment?.bodyClass||'cc-desk-home-surface');
      const shell=document.createElement('div');shell.className='app-shell page';
      if(fragment){
        const nav=document.createElement('header');nav.className='cc-desk-topnav';
        nav.innerHTML='<nav id="navigation" aria-label="Funzioni della sezione"></nav><button type="button" id="logout">Esci</button>';
        shell.append(nav);
        const pageBody=document.createElement('div');pageBody.innerHTML=fragment.page;
        shell.append(...pageBody.children);
        if(fragment.modal){const modal=document.createElement('div');modal.innerHTML=fragment.modal;section.append(...modal.children);}
      }else{
        shell.innerHTML=homeContent();
      }
      section.append(shell);
      root.replaceChildren(section);
      if(view==='home')loadHomeSummary(section);
      window.ccDeskSurfaceRoot=section;
      window.ccDeskNavigate=path=>navigate(path);
      if(surface)await import('/assets/centrochange_core/js/'+surface.script+'?ccdesk='+token);
      if(token!==generation)return;
      page.set_title('Centro Change · '+(items.find(([id])=>id===view)?.[1]||''));
      window.dispatchEvent(new Event('cc-desk-route-change'));
    }catch(error){if(token===generation){root.textContent='';const alert=document.createElement('p');alert.className='alert alert-danger';alert.setAttribute('role','alert');alert.textContent=error.message;root.append(alert);}}
  }
  root.addEventListener('click',event=>{
    const link=event.target.closest('a[href]');if(!link||!root.contains(link))return;
    const url=new URL(link.href,location.href);if(!routeByPath[url.pathname]&&url.pathname!=='/app/cc-unified-desk')return;
    event.preventDefault();event.stopImmediatePropagation();navigate(url.pathname+url.search);
  },true);
  frappe.pages['cc-unified-desk'].on_page_show=()=>{
    document.body.classList.add('cc-unified-desk-open');
    if(root.childElementCount)return;
    const args=new URLSearchParams(location.search),requested=args.get('cc_view')||'home';
    const view=Object.hasOwn(allowed,requested)&&allowed[requested]?requested:'home';
    if(view)navigate(view==='home'?routeUrl('home'):surfaces[view].path+'?'+args.toString());
    else root.textContent='Accesso non autorizzato.';
  };
  $(wrapper).on('hide',()=>{generation++;root.replaceChildren();window.ccDeskSurfaceRoot=null;window.ccDeskNavigate=null;document.body.classList.remove('cc-unified-desk-open');});
};
