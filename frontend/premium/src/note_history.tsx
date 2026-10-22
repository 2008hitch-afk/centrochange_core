import { type Row, displayDate } from './api'
import { Button, Empty } from './ui'

type Group = { id: string; latest: Row; earlier: Row[] }
const stamp = (row: Row) => {
  const raw = String(row.creation ?? '')
  return raw ? `${displayDate(raw)}${raw.length >= 16 ? ' · ' + raw.slice(11, 16) : ''}` : 'Data non disponibile'
}

function groups(rows: Row[]): Group[] {
  const byId = new Map(rows.map(row => [String(row.name), row]))
  const root = (row: Row) => {
    let current = row
    const visited = new Set<string>()
    while (current.corrects) {
      const parent = String(current.corrects)
      if (visited.has(parent)) break
      visited.add(parent)
      if (!byId.has(parent)) return parent
      current = byId.get(parent)!
    }
    return String(current.name)
  }
  const grouped = new Map<string, Row[]>()
  rows.forEach(row => { const id = root(row); grouped.set(id, [...(grouped.get(id) ?? []), row]) })
  return Array.from(grouped, ([id, revisions]) => {
    revisions.sort((a, b) => String(b.creation ?? '').localeCompare(String(a.creation ?? '')) || String(b.name).localeCompare(String(a.name)))
    return { id, latest: revisions[0], earlier: revisions.slice(1) }
  }).sort((a, b) => String(b.latest.creation ?? '').localeCompare(String(a.latest.creation ?? '')))
}

export function NoteHistory({ rows, onCorrect, privateNotes = false }: { rows: Row[]; onCorrect?: (row: Row) => void; privateNotes?: boolean }) {
  const notes = groups(rows)
  if (!notes.length) return <Empty title="Nessuna nota" />
  return <div className="note-groups">{notes.map(group => <article className={`note ${privateNotes ? 'private' : ''}`} key={group.id}>
    <div className="note-head"><strong>{group.latest.corrects ? 'Ultima rettifica registrata' : 'Nota registrata'}</strong><small>{stamp(group.latest)} · {String(group.latest.authored_by ?? 'Autore non disponibile')}</small></div>
    <p>{String(group.latest.content ?? '')}</p>
    {group.earlier.length > 0 && <details><summary>Cronologia precedenti ({group.earlier.length})</summary>{group.earlier.map(row => <div className="note-revision" key={String(row.name)}><small>{stamp(row)} · {String(row.authored_by ?? 'Autore non disponibile')}</small><p>{String(row.content ?? '')}</p></div>)}</details>}
    {onCorrect && <Button variant="ghost" onClick={() => onCorrect(group.latest)}>Rettifica</Button>}
  </article>)}</div>
}
