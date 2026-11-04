# Issue #156 — verifica coordinata e stato Factory

Owner GO: tracker #156, commento #6627551926. Perimetro: un solo account operativo Amministrazione/Direzione, sviluppo e test sintetici isolati; nessun deploy UAT, merge o produzione. PR #203 è stacked sulla PR draft #202 e richiede integrazione/approvazioni in ordine separato; `AUDIT-11` non viene marcato VERIFIED per consentire artificialmente questa attività. Il Goal `OPERATIONAL-156` è registrato ACTIVE con autorizzazione effettiva; non si inventano review, accettazioni o risultati live. Il validatore del progetto è strutturale; validate-goal resta intenzionalmente non superato finché mancano i gate e le prove indipendenti.

Verifica del commento #6630739943: il percorso di chiusura con importo positivo dovuto ora applica la stessa guardia sintetica dell'API di incasso. Colloqui gratuiti e stati non dovuti/coperti conservano il marcatore binario legacy senza creare un incasso monetario; replay e rettifiche di eventi legacy conservano lo storico. Un evento già allocato non può essere rettificato finché non esiste una procedura autorizzata di storno. La fattura attiva impedisce di creare un nuovo incasso operativo su quella seduta; la riconciliazione fiscale rimane fuori dal perimetro.

Catalogo UAT consultato in sola lettura nella verifica precedente: assente un Appointment Type 45 min / 44 EUR. Stato `NOT_READY_DEMO_SECOND_SESSION`; nessun servizio, tariffa o prenotazione duplicata creati. La configurazione richiede gate separato.

La verifica tecnica isolata non equivale a `PASS_LIVE UAT`, né a `OWNER_ACCEPTED`. Review indipendente e UX per tutte le interfacce restano da completare. La PR non autorizza alcun aggiornamento UAT, merge o deploy; la migrazione e il rollback richiedono il gate e il piano dedicati.

## Evidenza del ciclo di verifica

- `PASS_OFFLINE`: suite Python 203 test, 1 skip; typecheck React; controllo di parità sorgenti/manifest. Il test GPG passa nell'ambiente corrente con gpg-agent disponibile.
- `PASS_CLONE`: Frappe/MariaDB sintetici creati da zero, fixture test-owned; chiusura positiva gratuita, pacchetto riservato e rinuncia; replay e correzione di stato binario legacy; assenza di incassi monetari per tali stati; prova negativa ambiente non sintetico con rollback di stato e conteggi contabili; incassi parziali/multi-seduta, replay, eccedenza, fattura in bozza, ruoli, notifiche, concorrenza e HTTP/CSRF. Le prove sono in `finance/operational_receipts_acceptance.py` e `infra/issue156_http.py`; il job `issue156-isolated.yml` le ripete sulla SHA della PR.
- `PASS_LIVE UAT`: NOT_TESTED per questa versione. `OWNER_ACCEPTED`: PENDING per le modifiche della PR #203. L'accettazione precedente di AUDIT-11 non viene estesa a questo Goal.

Per rettifiche: il replay identico e la correzione di eventi binari storici non associati ad allocazioni restano supportati. Una richiesta di incasso su seduta collegata a fattura attiva e una modifica di un evento con allocazioni restano bloccate: sono necessarie riconciliazione e storno non ancora definiti, senza creare documenti contabili fittizi.
