// Presentation of existing lifecycle rules. The server remains authoritative.
export function sessionActions(row, roles, nowRome) {
  const managerial=roles.includes('CC Manager')||roles.includes('CC Secretariat')||roles.includes('Administrator');
  const date=String(row.appointment_date||''),time=String(row.appointment_time||'00:00:00');
  const start=new Date(`${date}T${time}Z`);
  const end=new Date(start.getTime()+Number(row.duration||0)*60000).toISOString().slice(0,19);
  const nextDay=new Date(`${date}T00:00:00Z`);
  nextDay.setUTCDate(nextDay.getUTCDate()+1);
  const cutoff=nextDay.toISOString().slice(0,10)+'T07:00:00';
  const closure=row.cc_closure_state||'Pending';
  const mutable=closure==='Reopened'||!['Closed','Auto Locked'].includes(closure)&&nowRome<cutoff;
  const open=!['Cancelled','No Show'].includes(row.status);
  return {
    close:mutable&&open&&nowRome>=end,
    move:mutable&&open&&date>=nowRome.slice(0,10)&&!(row.status==='Closed'&&closure!=='Reopened'),
    cancel:mutable&&open&&!row.cc_performed,
    reopen:managerial&&['Closed','Auto Locked'].includes(closure),
    waive:managerial&&['Due','Package Covered'].includes(row.cc_economic_state),
  };
}
