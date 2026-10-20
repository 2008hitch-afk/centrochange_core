// Calendar date for human-facing defaults. API and stored timestamps stay canonical.
export function romeToday(instant=new Date()) {
  const parts=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{
    timeZone:'Europe/Rome',year:'numeric',month:'2-digit',day:'2-digit'
  }).formatToParts(instant).map(part=>[part.type,part.value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}

// Human-facing formatting only. Keep API, database and fiscal timestamps intact.
// Frappe's naive Date/Datetime values are already in the Site's Europe/Rome
// wall time; only offset-bearing instants need timezone conversion.
const wall = value => String(value ?? '').match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?/);
const parts = instant => Object.fromEntries(new Intl.DateTimeFormat('en-GB', {
  timeZone:'Europe/Rome', year:'numeric', month:'2-digit', day:'2-digit',
  hour:'2-digit', minute:'2-digit', hourCycle:'h23'
}).formatToParts(instant).map(part => [part.type,part.value]));
function displayParts(value) {
  if (value instanceof Date || /(?:Z|[+-]\d{2}:?\d{2})$/.test(String(value ?? ''))) {
    const instant = value instanceof Date ? value : new Date(value);
    return Number.isNaN(instant.getTime()) ? null : parts(instant);
  }
  const match = wall(value);
  return match && {year:match[1],month:match[2],day:match[3],hour:match[4],minute:match[5]};
}
export function italianDate(value) {
  const p=displayParts(value);
  return p ? `${p.day}/${p.month}/${p.year}` : String(value ?? '');
}
export function italianDateTime(value) {
  const p=displayParts(value);
  return p && p.hour != null ? `${p.day}/${p.month}/${p.year} ${p.hour}:${p.minute}` : italianDate(value);
}
export function italianTime(value) {
  const p=displayParts(value);
  return p?.hour != null ? `${p.hour}:${p.minute}` : String(value ?? '').slice(0,5);
}
