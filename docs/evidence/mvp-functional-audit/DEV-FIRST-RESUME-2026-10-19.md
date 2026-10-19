# DEV-FIRST — verifica di ripresa 2026-10-19

Esito: **BLOCKED — candidato non più installato; rollback precedente completato**.

La verifica di ripresa è stata esclusivamente read-only sul DEV. Nessuna nuova installazione, cancellazione, fixture mutativa o rollback avviato durante questa verifica. Nessuna pubblicazione GitHub.

## Stato accertato

- Branch `audit/mvp-functional-completion`, HEAD iniziale `59be880`, worktree pulito.
- Ultimo run: `20261019T090909Z-2933275`, concluso `ROLLED_BACK`, nessun rollback_failure.
- Candidato provato: `0b399651b11e375fbf8ab0327fb4552877e1109c`, immagine `sha256:12f2d9f879a787053fefeb735c2d30c39fbb4695b47752e0a0a370d69a37abb7`.
- Runtime ripristinato: `centrochange-single:issue139-realtime-v2`, immagine `sha256:2054c8d2ffe887e56bfd0a5a2a867449286e97bee76380119d3c6fcdb9e68cbc`, sorgente `0380874fdf91c7fe191a93ec676e2c1d6f62ff7f`.
- Nove servizi attivi; DB e Redis healthy; ping HTTP 200.
- Preflight attuale PASS: configurazione, immagini, sei hook, CSS, risorse, Centro A attivo/B inattivo.
- Dati, schema e permessi coincidono esattamente con il checkpoint dell'ultimo run.
- Fingerprint dati: `caba48b14430cd975213fde6273aada780aecd6e6604ad4fbb5ccda8bfc4eae0`.
- Fingerprint Communication: `a13e25cf97b4bfa76856038614ec3e99380c086fc83c322db0958490ff19ac81`.
- Audit: 137 record. Nessun executor o runner browser dell'installazione ancora in corso.

## Risultati recuperati

Sul candidato, prima del rollback: 128/128 controlli browser, 22/22 coppie List/Form, Administrator, asset e Socket.IO PASS. Questi risultati non dimostrano i flussi POS e le altre sei capability. Sicurezza 38 e regressione finale non raggiunte. Matrice: 40 PASS storici, sei PARTIAL; nessuna promozione automatica a PASS live.

## Cause concrete

1. Preparazione fattura: `ValidationError: La seduta ha già una fattura nativa attiva.` La catena del runner chiama `incoming_acceptance.prepare_http` → `banking_acceptance.prepare_http` → `receivables_acceptance.prepare_http`. Il setup banca crea e contabilizza già due fatture, inclusa quella della prima seduta. Il successivo `prepare_browser_invoice` tenta di fatturare nuovamente quella seduta. Il blocco anti-duplicazione del prodotto è corretto; la composizione delle fixture è errata.
2. Primo flusso finance: cleanup PASS, classificato BLOCKED e l'executor continua correttamente.
3. Flusso native-reports: stesso errore di fattura, seguito da `frappe.exceptions.QueryDeadlockError` / MariaDB 1020 in `destroy_http`, riga 333, cancellazione delle sole entità fixture. La diagnostica conservata non identifica affidabilmente il concorrente responsabile. Il cleanup non è dimostrato completo: il rollback conservativo è quindi coerente con il gate di integrità, non con un semplice difetto grafico.
4. Il ripristino completo ha recuperato gli invarianti; la verifica indipendente di ripresa lo conferma.

## Confine operativo

Non si possono riprendere i soli test mancanti del candidato: il runtime ora espone la baseline precedente. Il mandato di ripresa vieta una nuova installazione. Nessun test mutativo aggiuntivo eseguito sulla baseline.

Prima di un futuro aggiornamento occorre correggere la composizione della fixture fattura (riuso esplicito della fattura sintetica preparata oppure seduta distinta posseduta dal test) e rendere verificabile la gestione della concorrenza nel cleanup, senza attenuare il controllo anti-duplicazione né ignorare un cleanup fallito. La causa precisa del conflitto DB resta da dimostrare; nessun PASS dichiarato.
