export async function api(method,args={},post=false){
  const url='/api/method/'+method;
  const options={credentials:'same-origin',headers:{Accept:'application/json'}};
  if(post){options.method='POST';options.headers['Content-Type']='application/json';options.headers['X-Frappe-CSRF-Token']=document.querySelector('meta[name=csrf-token]').content;options.body=JSON.stringify(args);}
  const response=await fetch(post?url:url+'?'+new URLSearchParams(Object.fromEntries(Object.entries(args).map(([key,value])=>[key,typeof value==='object'?JSON.stringify(value):value]))),options);
  const data=await response.json();
  if(!response.ok){
    let message='Operazione non riuscita. Verifica autorizzazioni e dati.';
    try{const messages=JSON.parse(data._server_messages||'[]');if(messages.length){const last=JSON.parse(messages.at(-1));message=last.message.replace(/<[^>]*>/g,'');}}catch{}
    if(response.status===403)message='Accesso negato: verifica assegnazione, centro e stato della seduta.';
    throw new Error(message);
  }
  return data.message;
}
export const operations=(method,args={},post=false)=>api('centrochange_core.operations.'+method,args,post);
export const scheduling=(method,args={},post=false)=>api('centrochange_core.scheduling.'+method,args,post);
export function escapeHtml(value){return String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));}
// getRandomValues also supports the isolated HTTP DEV origin; no weak random fallback.
export function requestKey(){return Array.from(crypto.getRandomValues(new Uint8Array(16)),value=>value.toString(16).padStart(2,'0')).join('');}
