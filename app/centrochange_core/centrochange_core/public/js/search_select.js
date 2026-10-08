import {clean,person} from './report_ui.js';
export const normalized=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('it-IT');
let sequence=0;
export function enhanceSelect(select,search=null){
 if(!select)return;
 const field=select.name||select.id,professional=field==='practitioner'||field==='professional-person'||field==='route';
 const rows=Array.from(select.options).filter(o=>o.value).map(o=>({name:o.value,label:professional?person(o.textContent):clean(o.textContent)}));
 const selected=select.value;
 select._searchGeneration=(select._searchGeneration||0)+1;
 if(select._combobox){select._combobox.configure(rows,selected,search);return;}
 const box=document.createElement('div');box.className='cc-combobox';
 const input=document.createElement('input');input.type='text';input.className='form-control';input.autocomplete='off';input.maxLength=140;
 const title='Cerca '+(professional?'professionista':'paziente');input.placeholder=title;input.setAttribute('aria-label',title);input.setAttribute('role','combobox');input.setAttribute('aria-autocomplete','list');input.setAttribute('aria-expanded','false');
 const list=document.createElement('div');list.className='dropdown-menu cc-options';list.id='cc-options-'+(++sequence);list.setAttribute('role','listbox');input.setAttribute('aria-controls',list.id);list.hidden=true;
 const status=document.createElement('small');status.className='form-hint';status.setAttribute('role','status');
 select.before(box);box.append(input,list,status);select.hidden=true;select.tabIndex=-1;select.setAttribute('aria-hidden','true');input.required=select.required;select.required=false;
 let original=[],matches=[],remote=null,active=-1,timer;
 const open=()=>{list.hidden=false;list.classList.add('show');input.setAttribute('aria-expanded','true');};
 const close=()=>{list.hidden=true;list.classList.remove('show');input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');};
 const highlight=index=>{active=index;list.querySelectorAll('[role=option]').forEach((o,i)=>{o.classList.toggle('active',i===index);o.setAttribute('aria-selected',String(i===index));});const o=list.querySelectorAll('[role=option]')[index];if(o){input.setAttribute('aria-activedescendant',o.id);o.scrollIntoView({block:'nearest'});}};
 const choose=row=>{if(!Array.from(select.options).some(o=>o.value===row.name))select.add(new Option(row.label,row.name));select.value=row.name;input.value=row.label;input.setCustomValidity('');close();select.dispatchEvent(new Event('change',{bubbles:true}));input.focus();};
 const render=(items,truncated=false)=>{matches=items;active=-1;list.replaceChildren();items.forEach((row,i)=>{const item=document.createElement('button');item.type='button';item.tabIndex=-1;item.className='dropdown-item';item.id=list.id+'-'+i;item.setAttribute('role','option');item.setAttribute('aria-selected','false');item.textContent=row.label;item.onmousedown=e=>e.preventDefault();item.onclick=()=>choose(row);list.append(item);});status.textContent=items.length?(items.length+(items.length===1?' risultato':' risultati')+(truncated?' · precisa la ricerca.':'')):'Nessun risultato autorizzato.';if(!items.length){const empty=document.createElement('div');empty.className='dropdown-item text-secondary';empty.textContent=status.textContent;list.append(empty);}open();};
 async function load(query){const id=++select._searchGeneration;status.textContent='Ricerca in corso…';input.setAttribute('aria-busy','true');try{const data=remote?await remote(query):null;if(id!==select._searchGeneration||!select.isConnected)return;render(data?data.patients.map(r=>({name:r.name,label:clean(r.patient_name)})):original.filter(r=>normalized(r.label+' '+r.name).includes(normalized(query))),data?.truncated);}catch{if(id===select._searchGeneration){list.replaceChildren();close();status.textContent='Ricerca non disponibile. Riprova.';}}finally{if(id===select._searchGeneration)input.removeAttribute('aria-busy');}}
 input.onfocus=()=>load(select.value?'':input.value);
 input.oninput=()=>{select.value='';input.setCustomValidity(input.value?'Seleziona un risultato autorizzato.':'');++select._searchGeneration;clearTimeout(timer);timer=setTimeout(()=>load(input.value),180);};
 input.onkeydown=e=>{if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(list.hidden){load(input.value);return;}highlight(Math.max(0,Math.min(matches.length-1,active+(e.key==='ArrowDown'?1:-1))));}else if(e.key==='Enter'&&!list.hidden){e.preventDefault();const row=matches[active<0?0:active];if(row)choose(row);}else if(e.key==='Escape'){e.preventDefault();close();}};
 input.onblur=()=>setTimeout(()=>{if(document.activeElement!==input){++select._searchGeneration;close();input.removeAttribute('aria-busy');}},150);
 select._combobox={input,configure(items,value,callback){++select._searchGeneration;clearTimeout(timer);original=items;remote=callback;input.value=items.find(r=>r.name===value)?.label||'';input.setCustomValidity('');status.textContent='';close();}};
 select._searchInput=input;select._searchStatus=status;select._combobox.configure(rows,selected,search);
}
export function enhanceSelectors(root,patientSearch=null){root.querySelectorAll('select[name="patient"],select[name="practitioner"]').forEach(select=>enhanceSelect(select,select.name==='patient'?patientSearch:null));}
