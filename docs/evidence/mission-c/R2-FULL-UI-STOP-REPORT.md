# Missione C #109 — continuazione R2, stop per OOM

**Esito: BLOCKED. READY_FOR_OWNER_UAT: NO.** Questo rapporto si aggiunge alle evidenze C1/C2/C3 e al precedente stop C109; non ne modifica l'esito storico. Esecuzione su laboratorio sintetico isolato, 9 ottobre 2026, 19:58–20:23 UTC.

## Revisione effettivamente provata

- Branch prodotto DRAFT PR #112: `issue-109/unified-desk-prototype`, HEAD `0c85d72d589c7eb59eca8ef949d18c87b9af2bc5`, stacked su PR #107; image finale C109 `sha256:1beab705b2511464212740a5fd2f87bc42ea64aff2b71058c35736392756c21e`. Frappe 16.50.0, ERPNext 16.50.0, Healthcare 16.6.1, Builder 1.35.1, pin R5 immutati. Nessun backend commerciale/contabile o permesso cambiato; unica modifica Python è lingua italiana dei sette utenti *del fixture sintetico*.
- Runtime dedicato `centrochange-c109`, site `b99.local`, URL durante i test `http://127.0.0.1:8109/app/cc-unified-desk`. Il guard ha arrestato il laboratorio: **l'URL ora non è disponibile**. RC22 `127.0.0.1:8082` ha risposto HTTP 200 prima e dopo.
- Le prove precedenti alla modifica di lingua sintetica (commit `0c85d72`) sono state eseguite sull'immagine `sha256:5a2f0cfff7b8046ef6014e38e771e4990faf3e2af085a007cd5c9c71d46e1935`. Il delta finale cambia solo `security/dev_acceptance.py` per i futuri fixture `it`; test Finance/TS/SdI e accesso nativo sono stati eseguiti sulla nuova immagine. I 69 controlli API non sono stati ripetuti sulla nuova immagine: non li si attribuisce a una suite R2 finale integralmente rieseguita.
- La Page Desk unica riusa i controller e i servizi canonici delle cinque aree Agenda, Finanza, Professionisti, Pazienti e Registro. Catalogo manager mediante le List/Form native già autorizzate. La webapp corrente resta primaria per DECISION-004; nessun cutover o link alla vecchia webapp come sostituto di una funzione interna.

## Test effettivamente eseguiti prima dello stop

| Verifica | Risultato |
|---|---|
| Login e bootstrap Desk, sette ruoli m/s/f/t/a/b/c, browser Chromium fresco per ruolo | PASS; A vede solo Alfa, B solo Beta, C nessuna seduta; Finance e Accountant entrano nelle viste autorizzate. |
| Navigazione tra cinque aree Desk, Direzione | PASS; 5/5 caricate senza errori JS. |
| Agenda/settimana/dettaglio Seduta–Storico–Note/booking dialog, cinque sezioni operative; nove viste Finance con documenti di Centro A e relativi dettagli; report e audit | PASS; 28 check browser Direzione senza alert/errori JS. |
| Segreteria, Finance, Accountant sulle nove viste Finance | PASS; 9/9 ciascuno, dati di Centro A; Accountant senza azioni di scrittura. |
| Browser mobile 390 px: Agenda, prenotazione, Finanza, Pazienti, ricerca paziente/professionista con tastiera | PASS; 4/4, `document.scrollWidth=390`, calendario scorre internamente. |
| Prenotazione sintetica 12/10, spostamento 13/10, cancellazione via UI Desk | PASS; servizi POST canonici e aggiornamento delle card. |
| Banca: import movimento sintetico e riconciliazione a fattura aperta via UI Desk | PASS; POST canonici e candidato sottostante. Un primo movimento della prova interrotta rimane non riconciliato nel solo laboratorio. |
| TS: versione READY preesistente, tentativo Accepted simulato; SdI: nuova preparazione e tentativo Accepted simulato | PASS; backend `TS ACCEPTED`, `SDI ACCEPTED_OR_DELIVERED`, `simulated=true`; nessun provider reale. |
| API negative e positive per 7 ruoli, centro incrociato, A/B/C, note riservate, query contabile e report/export | PASS, 69/69; risultati in `r2/security-results.json`. |
| List native manager aperte direttamente: Item, Item Price, Appointment Type, CC Center Service, CC Package Template, Patient, Healthcare Practitioner | PASS in accesso diretto 7/7; shell nativa usa la lingua utente `it`, ma alcune etichette dei DocType ERPNext/Healthcare restano inglesi. |
| Percorso *ripetuto* Desk → cinque pagine native Catalogo nello stesso browser QA | **FAIL / safety stop**: Chromium nel cgroup QA 512 MiB è stato OOM-killed prima del completamento. Nessun retry. |

## Matrice di stato delle 24 aree C1

`PASS` qui significa solo il controllo discriminante indicato sopra, non l'intera acceptance della sezione. `PARTIAL` richiede altre prove sulla UI finale.

| Area C1 | Stato R2 |
|---|---|
| Agenda settimanale | PASS |
| Prenota / sposta / cancella | PASS |
| Seduta / storico / note | PARTIAL: consultazione sì, scrittura note/chiusura/riapertura non provata R2 |
| Pazienti | PARTIAL: lista, ricerca, report e selettore sì; nuova anagrafica non provata R2 |
| Professionisti | PARTIAL: viste e isolamento sì; lifecycle non provato R2 |
| Disponibilità | PARTIAL: vista sì, cambio/assenza non provati R2 |
| Servizi / prezzi / pacchetti | PARTIAL: accesso diretto List nativa sì; flusso da Page fermato da OOM, scritture non provate |
| Contabilità / registri | PARTIAL: read/API e guard sì; tutte le interazioni native non provate |
| Fatture pazienti / fornitori | PARTIAL: liste/dettagli sì; pagamento/rettifica da Desk non provati |
| Incassi / pagamenti | PARTIAL: percorso bancario sì; Payment Entry da fattura non provato |
| Banca / riconciliazione | PASS per import + riconciliazione sintetici |
| Report Centro / Professionisti / Pazienti | PARTIAL: viste sì; tutti i drill-down/KPI riconciliati non provati R2 |
| Report contabili ERPNext generici per ruoli limitati | BLOCKED_BY_OWNER_DECISION, come C1: guard confermato; restano disponibili report CC scoped |
| SdI simulato | PASS per preparazione/queue/esito sintetici |
| TS simulato | PASS per queue/esito sintetici; revisione input non ripetuta R2 |
| Audit / registro | PARTIAL: vista sì, confronto completo con tutte le mutazioni R2 non provato |
| Amministrazione accessi / centri | PARTIAL: vista sì, lifecycle da Desk non provato R2 |
| Coda amministrativa / compensi | PARTIAL: viste sì, override/comparison da Desk non provati R2 |
| Notifiche / job | PARTIAL: vista sì, retry/worker non provati R2 |
| Login / logout | PARTIAL: login sette ruoli sì, logout non provato R2 |
| Sito pubblico / primo incontro | NOT_APPLICABLE_PUBLIC_DEV: sito separato, escluso dalla conversione Desk |
| Stampa / export | PARTIAL: guard negativi sì, positivi/UI non provati R2 |
| Validazione DEV | NOT_APPLICABLE_PUBLIC_DEV: guida tecnica separata |
| Cutover / identità globale Desk | BLOCKED_BY_OWNER_DECISION, fuori Missione C; DECISION-004 invariata |

## Stop e isolamento

Il browser QA `centrochange-c109-r2-browser-m-1791577406` ha `OOMKilled=true`, limite 536870912 byte. Il monitor ha registrato incremento OOM host/cgroup da 6 a 7 alle 20:23 UTC ed ha arrestato **solo** i container C109, lasciando intatti volumi, database, immagini e checkpoint. MemAvailable host nell'ultimo campione ~5.07 GiB, PSI memoria full 0%, PSI I/O full 0.66%: il limite locale QA, non carenza host generalizzata, è la causa discriminante. La somma dei limiti runtime+QA non è mai stata alzata da 2.5 GiB. Disco finale 12,774,600,704 byte circa, sopra riserva 4 GiB.

Inventario protetto: 137/137 container invariati per image, stato, avvio e restart count. RC22: 9 container attivi, HTTP 200 dopo lo stop. Nessun merge, upgrade RC22, invio provider, dato reale o modifica alla produzione.

**Gate residuo specifico:** il §7.3(5) del piano #110 impone stop immediato per un nuovo OOM e vieta retry non controllati. Per riprendere serve una nuova attivazione di sicurezza. La soluzione minima proposta è suddividere il test Catalogo in un Chromium fresco *per pagina nativa* mantenendo QA 512 MiB, runtime 2 GiB e tetto aggregato 2.5 GiB, poi completare le prove PARTIAL. Un eventuale passaggio a QA 768 MiB richiede prima misura e redistribuzione interna runtime a 1792 MiB, senza modificare le soglie PSI/OOM. Nessuna di queste azioni è stata eseguita dopo lo stop.

Screenshot, script browser, risultati sintetici e `R2-STOP.json` sono nella directory `r2/`; fixture/credenziali e log grezzi restano fuori Git. Gli script leggono un fixture JSON privato del laboratorio a runtime, senza valori incorporati.
