/* Unified Desk host: mount the existing authorized Centro Change controllers in one Desk Page.
 * No second backend, patient master, ledger, permission path or website navigation is created.
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
  const canAudit=roles.has('CC Manager');
  const allowed={agenda:canOperate,finance:canFinance,professional:canFinance,patient:canFinance,audit:canAudit};
  const items=[['agenda','Agenda'],['finance','Finanza'],['professional','Professionisti'],['patient','Pazienti'],['audit','Registro modifiche']];
  let generation=0,active=null;
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
  function routeUrl(view,params){const u=new URL(location.href);u.search='';u.searchParams.set('cc_view',view);new URLSearchParams(params||'').forEach((v,k)=>u.searchParams.set(k,v));return u.pathname+u.search;}
  async function navigate(path,replace=true){
    const u=new URL(path,location.origin),view=routeByPath[u.pathname];
    if(!view){if(u.pathname.startsWith('/login'))location.href=u.href;return;}
    if(!allowed[view]){root.textContent='Accesso non autorizzato.';return;}
    const token=++generation;active=view;root.textContent='Caricamento…';
    if(replace)history.replaceState(null,'',routeUrl(view,u.search));
    try{
      const surface=surfaces[view];
      const response=await fetch(surface.path+u.search,{credentials:'same-origin',redirect:'follow'});
      if(!response.ok||new URL(response.url).pathname.startsWith('/login'))throw new Error('Accesso non autorizzato nel contesto richiesto.');
      const doc=new DOMParser().parseFromString(await response.text(),'text/html');
      const shell=doc.querySelector('.app-shell'),main=doc.querySelector('#cc-main');
      if(!shell||!main)throw new Error('Vista Centro Change non disponibile.');
      for(const file of surface.css)await css(file);
      if(token!==generation)return;
      const section=document.createElement('section');section.className='cc-desk-surface '+(doc.body.className||'');
      shell.querySelector('.sidebar')?.remove();
      let links=items.filter(([id])=>allowed[id]).map(([id,text])=>`<a href="${surfaces[id].path}" class="cc-desk-route ${id===view?'active':''}">${text}</a>`).join('');
      if(roles.has('CC Manager'))links+='<details class="cc-desk-catalog"><summary>Catalogo</summary><div><a href="/app/item">Servizi</a><a href="/app/item-price">Tariffe</a><a href="/app/appointment-type">Tipi di seduta</a><a href="/app/cc-center-service">Servizi del centro</a><a href="/app/cc-package-template">Modelli pacchetto</a></div></details>';
      const routebar=document.createElement('nav');routebar.className='cc-desk-routebar';routebar.setAttribute('aria-label','Aree Centro Change');routebar.innerHTML=links;
      const nav=document.createElement('header');nav.className='cc-desk-topnav';
      nav.innerHTML='<nav id="navigation" aria-label="Funzioni della sezione"></nav><button type="button" id="logout">Esci</button>';
      shell.prepend(nav);section.append(routebar,shell);
      const dialog=doc.querySelector('#modal');if(dialog)section.append(dialog);
      root.replaceChildren(section);
      window.ccDeskSurfaceRoot=section;
      window.ccDeskNavigate=path=>navigate(path);
      await import('/assets/centrochange_core/js/'+surface.script+'?ccdesk='+token);
      if(token!==generation)return;
      page.set_title('Centro Change · '+(items.find(([id])=>id===view)?.[1]||''));
    }catch(error){if(token===generation){root.textContent='';const alert=document.createElement('p');alert.className='alert alert-danger';alert.setAttribute('role','alert');alert.textContent=error.message;root.append(alert);}}
  }
  root.addEventListener('click',event=>{
    const link=event.target.closest('a[href]');if(!link||!root.contains(link))return;
    const url=new URL(link.href,location.href);if(!routeByPath[url.pathname])return;
    event.preventDefault();event.stopImmediatePropagation();navigate(url.pathname+url.search);
  },true);
  frappe.pages['cc-unified-desk'].on_page_show=()=>{
    if(root.childElementCount)return;
    const args=new URLSearchParams(location.search),requested=args.get('cc_view')||'agenda';
    const view=allowed[requested]?requested:Object.keys(allowed).find(k=>allowed[k]);
    if(view)navigate(surfaces[view].path+'?'+args.toString());
    else root.textContent='Accesso non autorizzato.';
  };
  $(wrapper).on('hide',()=>{generation++;root.replaceChildren();window.ccDeskSurfaceRoot=null;window.ccDeskNavigate=null;});
};
