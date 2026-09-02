# Centro Change — Technical Architecture Baseline

**Stato:** PROPOSTA / RUNTIME VALIDATION REQUIRED

Questo documento traduce la baseline tecnica corrente in una forma operativa per sviluppo e test. Le scelte che dipendono dal comportamento reale di Frappe/ERPNext/Builder devono essere confermate tramite spike.

## 1. Stack candidato

- Frappe Framework v16 (versione esatta da validare runtime)
- ERPNext v16 (versione esatta da validare runtime)
- Frappe Builder compatibile
- custom app `centrochange_core`
- Marley Health: solo spike di fit, non dipendenza decisa

## 2. Ownership

### Frappe/ERPNext master dove il fit è corretto

- User / autenticazione / ruoli base
- Contact
- Customer come identità economico-amministrativa del paziente, se confermato
- Item / Item Group per prestazioni
- Item Price / Price List
- Mode of Payment
- Email Account / Communication / Notification
- report / print / export infrastructure
- futura Sales Invoice / Payment Entry / Payment Ledger solo quando verrà attivata vera contabilità

### Centro Change master

- assegnazione paziente-professionista
- note organizzative
- note professionali riservate
- regole calendario specifiche non coperte adeguatamente dal nativo
- chiusura giornaliera
- settlement operativo MVP
- pacchetti e ledger
- regola 48h
- audit business specifico
- permission logic dinamica
- snapshot storici di servizio/durata/prezzo applicati alla seduta

## 3. Principi di estensione

Ordine di preferenza:

1. native Frappe/ERPNext;
2. estensione supportata del nativo;
3. app ufficiale pertinente;
4. custom `centrochange_core`;
5. integrazione esterna.

Sono da evitare:

- fork del core;
- monkey patch non supportate;
- modifica manuale di container running come soluzione persistente;
- business logic critica solo in configurazioni non versionate;
- controlli di autorizzazione solo lato UI.

## 4. Modello professionista candidato

```text
User
├── Employee (se utile)
├── CC Professional oppure Healthcare Practitioner
└── Sales Person opzionale come proiezione economica
```

`Sales Person` non è identità operativa né meccanismo di sicurezza.

## 5. Prestazioni e prezzi

Riutilizzare Item / Item Price / Price List se confermato dal runtime.
Ogni appuntamento deve conservare snapshot di:

- prestazione/nome applicato;
- durata applicata;
- prezzo applicato.

## 6. Pagamenti MVP

L'MVP non registra automaticamente una `Payment Entry` quando un professionista indica “Pagato Sì”.

Modello candidato `CC Settlement`:

- riferimento seduta/pacchetto;
- amount snapshot;
- paid yes/no;
- Mode of Payment;
- autore/data consolidamento;
- audit;
- eventuale riferimento futuro a Sales Invoice / Payment Entry.

Path futuro:

```text
CC Settlement → Sales Invoice → Payment Entry → Payment Ledger
```

## 7. Pacchetti

Custom in `centrochange_core`, senza forzare Product Bundle/Subscription se la semantica non coincide.

Modello candidato:

- `CC Package Template`
- `CC Package Template Line`
- `CC Patient Package`
- `CC Package Ledger`

Eventi minimi ledger:

- RESERVE
- RELEASE
- CONSUME
- ADMIN_ADJUSTMENT

Richiesti idempotenza e controllo concorrenza.

## 8. Note e segregazione

Separare fisicamente:

- `CC Organizational Note`
- `CC Professional Note`

La segregazione deve valere su UI, API, report, export e accesso diretto.

## 9. Calendario / appointment

Non assumere che ERPNext `Appointment` standard sia adatto.
Prima di creare DocType custom per Patient/Practitioner/Appointment/Availability va eseguito lo spike Marley Health.

Requisiti non negoziabili:

- primo incontro pubblico solo con Marco/Francesca;
- sedute successive solo backend;
- professionista opera solo sui pazienti assegnati;
- no double booking;
- disponibilità/indisponibilità;
- concorrenza sullo slot;
- storico cancellazioni/spostamenti;
- snapshot economico/storico.

## 10. Chiusura giornaliera

Business logic custom sopra scheduler/queue Frappe.

Modello candidato `CC Session Closure`:

- Pending
- Closed
- Auto Locked
- Reopened/Corrected

Automazioni:

- 21:00 reminder solo se pendenti;
- 07:00 giorno successivo auto-lock;
- sblocco solo ruoli autorizzati;
- regola 48h centralizzata e testabile.

## 11. Website/UI

### Builder / Website
Per sito pubblico branded, contenuti e funnel di prenotazione iniziale.

### Desk / Workspace / Form / List / Report
Preferire per backoffice standard quando l'UX è sufficiente.

### UI custom mirate
Solo dove portano valore operativo chiaro:

- calendario multi-professionista;
- chiusura giornaliera;
- scheda paziente unificata;
- dashboard direzionale.

## 12. Ambienti

Pattern candidato:

```text
Windows / WSL2 / Docker
├── altri stack locali                [isolati]
└── centrochange-dev                  [nuovo Compose project]
    ├── DB dedicato
    ├── Redis dedicato
    ├── site volume dedicato
    ├── network dedicata
    └── image Centro Change dedicata
```

Il riuso è di pattern/tooling, non di stato applicativo o codice client-specific.

## 13. Gate

Prima del feature development esteso chiudere gli spike critici su:

1. runtime baseline / reuse & isolation;
2. Marley Health fit;
3. permission model;
4. double booking;
5. Builder/Git reproducibility;
6. package ledger;
7. scheduler 21:00/07:00;
8. settlement vs ERP accounting;
9. reporting/export permissions;
10. backup/restore.
