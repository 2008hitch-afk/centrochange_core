# Copertura — inventario minimo, NON equivale a implementazione

Fonti: HC-0005 DECISION-060/061; issue #148 e #75/#79/#134/#135/#136/#137/#139. Gli stati si verificano da GitHub prima dell'esecuzione.

| Area | Flussi da mappare | Evidenza |
|---|---|---|
| Avvio | login, Agenda landing, ruolo attivo, logout | #75 |
| Agenda | settimana/giorno, professionisti, prenota, sposta, cancella, chiudi/riapri se lecito, 48h, stato/storico seduta | #136 |
| Pazienti | search, scheda, note, storia, pacchetti, assegnazioni | #136 |
| Professionisti | schede, disponibilità, assignment, visibility | #136 |
| Finanza | sales/purchase invoices, incassi, movimenti bancari, riconciliazioni, compensi e report | #136 |
| Catalogo | Item/Item Price, Appointment Type, servizi centro, template pacchetto | #136 |
| Backoffice | report, notifications, access control, audit, TS/SdI simulated | #75, #134 |
| Pubblico | primo incontro Guest autorizzato, selezione e guards | baseline MVP |
| Ruoli | Direzione, Segreteria, Finanza, Commercialista, professionisti, Guest, secondo matrice canonica | #137 |

## 11 route/aree rotte nell'Owner UAT del 14/10/2026

1. Fatture pazienti (`/desk/accounts/sales-invoice`)
2. Fatture professionisti (`/desk/accounts/purchase-invoice`)
3. Incassi/pagamenti (`/desk/accounts/payment-entry`)
4. Movimenti bancari
5. Anagrafica pazienti
6. Anagrafica professionisti
7. Catalogo servizi (`/desk/stock/item`)
8. Tariffe (`/desk/stock/item-price`)
9. Tipi seduta (`/desk/healthcare/appointment-type`)
10. Servizi del centro
11. Modelli pacchetto

Tutte richiedono evidenza **sia per la lista sia per la scheda/form** o segregazione motivata nel solo Desk tecnico autorizzato, con ruolo e test. Le precedenti 128 combinazioni browser e 38 negative security sono baseline storiche da rieseguire, non una condizione già PASS.

## Stati da non confondere

- Issue #23 `closed` vs manifest `GOAL-02 AUTHORIZED_ACTIVE`: discordanza, non correggere automaticamente.
- Missione C #109 sospesa, PR #112 DRAFT; #139 precedente remediation/harness isolato. Non riprenderle come due frontend concorrenti.
- GOAL-03, produzione, dati reali, SdI/TS reali, terza installazione DEV condivisa non autorizzati.
- La skill non è evidenza che React sia implementato; una PR DRAFT con la skill non è una installazione runtime.
