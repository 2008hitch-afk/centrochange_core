import {clean,person} from './report_ui.js';
export const normalized=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('it-IT');
export function enhanceSelect(select,search=null){
  if(!select)return;const field=select.name||select.id,professional=field==='practitioner'||field==='professional-person';
  Array.from(select.options).forEach(o=>{if(o.value)o.textContent=professional?person(o.textContent):clean(o.textContent);});
  let input=select._searchInput,status=select._searchStatus;
  if(!input){input=document.createElement('input');input.type='search';input.placeholder='Cerca '+(professional?'professionista':'paziente');input.setAttribute('aria-label',input.placeholder);input.className='selector-search';status=document.createElement('small');status.setAttribute('role','status');select.before(input);select.after(status);select._searchInput=input;select._searchStatus=status;}
  input.value='';status.textContent='';let original=Array.from(select.options).filter(o=>o.value).map(o=>({name:o.value,label:o.textContent})),timer;select._searchGeneration=(select._searchGeneration||0)+1;
  const render=(rows,truncated=false)=>{select.replaceChildren(new Option('Seleziona',''),...rows.map(r=>new Option(r.label,r.name)));status.textContent=rows.length?(rows.length+' risultati'+(truncated?' · precisa la ricerca.':'')):'Nessun risultato autorizzato.';};
  input.oninput=()=>{const id=++select._searchGeneration,query=input.value;select.value='';clearTimeout(timer);timer=setTimeout(async()=>{try{if(search){const data=await search(query);if(id!==select._searchGeneration||!select.isConnected)return;render(data.patients.map(r=>({name:r.name,label:clean(r.patient_name)})),data.truncated);}else{const match=normalized(query);render(original.filter(r=>normalized(r.label+' '+r.name).includes(match)));}}catch{if(id===select._searchGeneration&&select.isConnected)status.textContent='Ricerca non disponibile. Riprova.';}},180);};
}
export function enhanceSelectors(root,patientSearch=null){root.querySelectorAll('select[name="patient"],select[name="practitioner"]').forEach(select=>enhanceSelect(select,select.name==='patient'?patientSearch:null));}
