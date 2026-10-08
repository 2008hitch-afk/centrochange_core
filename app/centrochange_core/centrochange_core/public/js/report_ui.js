import {escapeHtml as esc} from './api.js';
export const clean=v=>String(v||'').replace(/^CC-HTTP-[A-Za-z0-9]+\s+/,'');
export const person=v=>({a:'Alfa',b:'Beta',c:'Gamma'}[clean(v)]||clean(v));
export const money=(n,c='EUR')=>n===null||n===undefined?'Da verificare':new Intl.NumberFormat('it-IT',{style:'currency',currency:c}).format(n);
const iso=d=>[d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');
export function preset(value,prefix="professional"){const today=new Date(new Date().toLocaleDateString('en-CA',{timeZone:'Europe/Rome'})+'T12:00:00'),a=new Date(today),b=new Date(today);if(value==='week'){a.setDate(a.getDate()-(a.getDay()+6)%7);b.setTime(a.getTime());b.setDate(b.getDate()+6);}if(value==='month'){a.setDate(1);b.setMonth(b.getMonth()+1,0);}if(value==='last-month'){a.setMonth(a.getMonth()-1,1);b.setDate(0);}document.querySelector('#'+prefix+'-start').value=iso(a);document.querySelector('#'+prefix+'-end').value=iso(b);}
export function table(rows,columns){return '<div class="table-wrap"><table><thead><tr>'+columns.map(([k,l])=>'<th>'+esc(l)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+columns.map(([k,l])=>'<td>'+esc(row[k]??'Da verificare')+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
export function metric(label,value,target){return '<button type="button" class="metric" data-drill="'+target+'"><span>'+esc(label)+'</span><strong>'+esc(value)+'</strong></button>';}
