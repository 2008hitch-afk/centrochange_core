// Native date semantics/picker retained; visible representation is always Italian.
export function enhanceDates(root=document){root.querySelectorAll('input[type="date"]:not(#week-date)').forEach(input=>{
  let label=input._dateDisplay;
  if(!label){const wrapper=document.createElement('span');wrapper.className='date-control';label=document.createElement('span');label.className='date-display';label.setAttribute('aria-hidden','true');input.before(wrapper);wrapper.append(label,input);input._dateDisplay=label;input.addEventListener('input',()=>update(input,label));input.addEventListener('change',()=>update(input,label));input.addEventListener('click',()=>{try{input.showPicker?.();}catch{}});}
  update(input,label);
});}
function update(input,label){label.textContent=/^\d{4}-\d{2}-\d{2}$/.test(input.value)?input.value.split('-').reverse().join('/'):'gg/mm/aaaa';}
