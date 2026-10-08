# Known Limitations Register — GOAL-02

Scope: DEV UAT sintetica autorizzata da DECISION-056. Nessun blocker critico noto di integrità o sicurezza nei controlli attuali, subordinato alle evidenze della build nel manifest. Le condizioni dimostrative sospese/mancanti sono risultati attesi, non defect nascosti.

| ID | Limite / impatto | Gestione / autorità | Stato |
|---|---|---|---|
| KL-01 | Nessuna validazione fiscale/contabile professionale, soggetti/indirizzi/tasse dimostrativi non utilizzabili realmente. | Solo prova sintetica; verifica commercialista prima dell’uso reale sotto gate separato. | OPEN — fuori dal gate UAT sintetico |
| KL-02 | SdI e TS puro adapter simulato; nessun provider, credential o protocollo reale. Accettazione simulata non dimostra trasporto/compliance. | Mantenere `SIMULATED` e domini separati; nessuna attivazione reale. | OPEN — gate futuri invariati |
| KL-03 | Email notifiche/blocco simulata, niente SMTP/SMS/gateway reale. | Verificare traccia locale e notifica interna, non consegna esterna. | EXPECTED |
| KL-04 | Dataset storico fisso settembre/ottobre 2026. Prenotazioni nuove seguono ora reale; lo slot iniziale 12/10/2026 scade nel tempo. | Scegliere slot futuri. Nuove date del dataset richiedono versione/candidate nuova, non scorrimento silenzioso. | EXPECTED |
| KL-05 | Determinismo semantico, non byte-identità DB: nomi seriali, timestamp, payload che contengono ID e password variano fra reset. | Confrontare hash normalizzato e manifest logico; conservare ID correnti solo nel DEV privato. | EXPECTED |
| KL-06 | Reset elimina solo fixture con prefisso esatto e ownership verificata. Dati sintetici creati fuori dal prefisso non vengono cancellati automaticamente. | Usare identità/UID demo della guida. Non estendere la cancellazione a dati sconosciuti. | EXPECTED |
| KL-07 | Prove modificative non indipendenti: incasso Beta cambia il match bancario; revoca accessi cambia disponibilità. | Rollback isolato per regressioni; preservare il dataset Owner, mai sovrascrivere automaticamente azioni cliente su seed replay. | EXPECTED |
| KL-08 | Site locale HTTP/DEV, hostname `.local`, accesso di rete cliente non predisposto. | URL/account consegnati dall’operatore in DEV autorizzato; nessuna pubblicazione/produzione implicita. | OPEN — non un blocker della preparazione UAT locale |
| KL-09 | Backup integro del GOAL-01 riusato come evidenza storica; restore/DR/produzione non provati dal pacchetto UAT. | Non dichiarare DR. I gate della roadmap successivi rimangono invariati. | OPEN — gate futuri |
| KL-10 | Grandezza report/agenda/API limitata e nessuna qualifica di carico o browser multi-engine. | Filtri espliciti; QA Chromium desktop/mobile pinned. Non assumere supporto prestazionale oltre dati testati. | EXPECTED |
| KL-11 | Zeta conserva le configurazioni mancanti previste. Alfa è stata modificata dalla Owner UAT: override e compensi correnti OK; la posizione sospesa precedente resta storica. | Configurazione demo/override solo direzione e audit; non inventare default, compenso zero o regola nuova. | EXPECTED |
| KL-12 | Client UAT in corso; accettazione finale GOAL02 ancora pendente. Stack draft non fuso. | Registrare esiti cliente separati e review PR. Nessun merge automatico o GOAL-03. | IN_PROGRESS / FINAL ACCEPTANCE PENDING |

Defect risolto: #59, risposta agenda precedente che sovrascriveva la vista Pazienti. Evidenza discriminante FAIL prima/PASS dopo e regressione persistente in UAT Evidence Package.

October7 remaining gates: #64 profile review; #76 explicit identity decision; #77 matrix review; #75 visual Owner walkthrough. Optional public Francesca route is not configured; readable unavailable state retained without seeding. Cross-client knowledge repository inaccessible (API404): supplementary learning extraction/publishing remains pending before final goal completion.
