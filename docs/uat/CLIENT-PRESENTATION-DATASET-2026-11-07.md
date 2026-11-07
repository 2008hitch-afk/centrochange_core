# Centro Change — Dataset di presentazione, novembre 2026

**STATO ATTUALE — 07/11/2026: STAGING POPOLATO E VERIFICATO DA CODEX.** La SHA realmente installata è `254af1505dc56ae9123ce64469f856cefabf61d4`; GitHub conferma **CI 3/3 PASS su questa SHA**. Codex riporta backup cifrato verificato e ripristinato su clone, `plan READY / apply PASS / inspect PASS`, conteggi **4/18/17/35**, 10 ricevute operative per **392 €**, zero documenti fiscali/email/SMS e smoke desktop/mobile PASS. Il flag `cc_presentation_seed` risulta disattivato dopo il caricamento. **Non eseguire nuovamente la procedura di importazione**: i passi sottostanti sono conservati come storico operativo e per eventuale nuova autorizzazione. La precedente SHA `51ed781b16550a0fd93aee968f44c3d761534429` è superata sullo STAGING. **Produzione invariata; PR #205 resta DRAFT senza merge.**

## Regole approvate

- 4 professionisti con account Frappe personali distinti, abilitati, collegati alla sede. I loro recapiti iniziali sono `@presentation.example.invalid`; **non sono account consegnabili**. Quando l'Owner comunicherà le email reali, si userà il servizio autorizzato di cambio login, senza sostituire le anagrafiche professionali.
- 18 pazienti con nomi italiani inventati, date di nascita fittizie e senza telefoni reali. 16 intestatari fiscali corrispondono al paziente; Alice Caruso e Pietro Caruso sono collegati a **un solo intestatario distinto**, Laura Caruso: 17 Customer unici. Nessun codice fiscale italiano verosimile o dato sanitario reale viene creato.
- 35 appuntamenti dal 12 ottobre al 18 novembre 2026: 10 colloqui iniziali da 20 minuti a €0 e 25 sedute da 45 minuti a €44. Nessuna sovrapposizione professionista/paziente.
- Storico sedute ordinarie: 8 pagate (€352), 2 parziali (€20 ciascuna, residuo €24 ciascuna), 3 da incassare (€44 ciascuna), 2 annullate senza addebito, 3 con esito da registrare; 7 future. Totale ricevute **operative**: €392, non fatturato fiscale. I colloqui: 7 storici chiusi gratuitamente e 3 futuri. Le future non devono generare automaticamente scaduti.
- **Nessuna fattura, Payment Entry contabile, GL Entry, SdI, Sistema TS, email o SMS**. Le sole registrazioni economiche previste sono `CC Operational Receipt` e `CC Economic Source Link`, contabilmente non trasmesse.
- Nessuna dicitura «Demo», «Test» o «Prova» nei nomi visibili. Il contrassegno di appartenenza vive **solo** in UID interni, recapiti non recapitabili e manifesto privato.
- Un solo branch/sede **già esistente** e operativa, scelta esplicitamente dal responsabile; non creare nuove sedi. Non ripristinare o eliminare record preesistenti.

**Unica ricetta dati:** `app/centrochange_core/centrochange_core/uat/presentation_dataset_v1.json`. Validazione offline: `python3 infra/verify_presentation_dataset.py`. Caricatore bench: `centrochange_core.uat.presentation_seed`, non accessibile via HTTP.

## Blocco prima della scrittura (obbligatorio)

1. **Clone isolato dello STAGING**: applicare codice e migrazioni della PR; eseguire `plan`, `apply`, `inspect` e prove reali di agenda, anagrafica fiscale, Report professionista/cliente e incassi. Verificare valori €0/20m e €44/45m, 17 Customer, 35 appuntamenti, email zero, documenti fiscali zero. Ripristinare/eliminare **solo il clone** al termine. Un semplice test offline o una CI 3/3 PASS **non sostituisce** il collaudo del caricamento.
2. CI e manifest del branch allineati. Non cambiare produzione o fare merge in main.
3. Prima dello STAGING: effettuare e verificare realmente un **backup cifrato**. Il suo SHA-256 è attestato nella configurazione; tale attestazione non sostituisce il controllo del backup. Confermare che il DB live sia ancora vuoto per Patient, Healthcare Practitioner, Customer, Patient Appointment, CC Operational Receipt, CC Economic Source Link, Sales Invoice, Payment Entry, GL Entry.
4. Verificare configurazione della sede esistente: due primi colloqui distinti e validi (in sede/online, ciascuno €0/20m), una sola Seduta €44/45m, prezzi EUR, fascia settimanale disponibile, `Mode of Payment: Contanti` attivo, società `Centro Change SYNTHETIC DEV` predefinita. Se non coincidono, **fermarsi**: non forzare silenziosamente importi, tipi di appuntamento o configurazioni del cliente.
5. L'importazione del calendario è valida **solo prima del 9 novembre 2026**. Se posticipata, revisionare date e rifare i test. Il sistema deve rifiutare ricette scadute.

## Correzione prerequisiti STAGING — 07/11/2026

Il primo tentativo di Codex ha correttamente **bloccato l'importazione senza modificare lo STAGING**. Erano assenti il gruppo Customer predefinito, il metodo di pagamento Contanti abilitato e `mute_emails=1`. Il sito offre inoltre due tipi nativi di primo colloquio (**in sede e online**), entrambi necessari alla prenotazione pubblica: **non cancellarne o disattivarne nessuno per far passare il caricatore**.

Procedura di riconciliazione **solo STAGING, dopo verifica del nome site e backup cifrato verificato**, senza record anagrafici:

1. ERPNext → `Customer Group`: scegliere o creare la categoria foglia `Clienti Centro Change` (`is_group=0`), sotto una radice già valida. In `Selling Settings` impostarla come gruppo clienti predefinito. Non cambiare la società e non creare Customer veri.
2. ERPNext → `Mode of Payment`: abilitare il metodo `Contanti` di tipo `Cash`, o crearlo **soltanto se assente**; non registrare pagamenti, fatture o movimenti contabili.
3. Configurazione **del solo site STAGING**, senza toccare `common_site_config.json` o la produzione: `bench --site "$SITE" set-config mute_emails 1`; verificare SMS Healthcare e qualsiasi trasmissione TS/SdI già disabilitati. Il loader deve arrestarsi se invii email o SMS risultano abilitati.
4. Con i due servizi pubblici già collegati tramite `cc_public_first_meeting_types.sede` e `.online`, mantenere entrambi attivi in `CC Center Service` nella sede selezionata, durata 20m e prezzo €0 EUR. Rendere i nomi **dei rispettivi Item** leggibili: `Primo colloquio conoscitivo in sede` e `Primo colloquio conoscitivo online`. Non cambiare ID dei tipi, i collegamenti pubblici o i prezzi. Il loader ora convalida entrambe le modalità e usa esplicitamente **in sede** per le dieci prenotazioni della presentazione. `Seduta` deve restare l'unica corrispondenza attiva a €44 EUR / 45m.
5. Riprovarne la sola fase di `plan` (nessuna scrittura). Se manca una mappatura pubblica o resta un catalogo ambiguo, non forzare e non creare duplicati. Solo dopo preflight PASS e conferma CI sulla nuova SHA procedere a `apply` una volta.

Non usare script che alterino la produzione; verificare sempre `site_config` e sede prima di ogni comando `set-config`. **Non confondere modifica delle impostazioni preliminari con completamento dell'importazione.**

## Procedura storica di primo caricamento — GIÀ ESEGUITA, NON RIPETERE

Da parte dell'operatore con accesso al server, con identificativo del vero *site* Frappe (non indovinare il nome) e SHA-256 del backup già cifrato/verificato:

```bash
bench --site "$SITE" set-config cc_presentation_seed 1
bench --site "$SITE" set-config cc_presentation_site "$SITE"
bench --site "$SITE" set-config mute_emails 1
bench --site "$SITE" set-config cc_presentation_backup_sha256 "$BACKUP_SHA256"
# cc_synthetic_dev deve già essere 1: non attivarlo su siti reali o produzione.
bench --site "$SITE" execute centrochange_core.uat.presentation_seed.plan --kwargs "{\"center\":\"$CENTER\"}"
# Trascrivere l'intero digest del piano e approvarlo esplicitamente.
bench --site "$SITE" execute centrochange_core.uat.presentation_seed.apply --kwargs "{\"center\":\"$CENTER\",\"approval_sha256\":\"$DATASET_SHA256\",\"backup_sha256\":\"$BACKUP_SHA256\"}"
bench --site "$SITE" execute centrochange_core.uat.presentation_seed.inspect
bench --site "$SITE" set-config cc_presentation_seed 0
# Soltanto dopo collaudo specifico sul clone e verifiche invii disabilitati:
bench --site "$SITE" set-config cc_presentation_intake 1
```

Il caricatore richiede `Administrator`, nome site esatto, `cc_synthetic_dev=1`, email disattivate, SMS e tariffa d'ingresso disabilitati, database inizialmente vuoto e digest approvato. Gestisce un lock esclusivo, transazioni, rollback, un manifesto locale 0600 e replay senza duplicazione. **Non** esporre `apply` come endpoint web. Non è previsto un reset automatico: in caso di errore, procedere solo con ripristino da backup o procedura di pulizia limitata ai record identificati e approvata separatamente.

## Verifica UI prima della presentazione

Controllare su desktop e mobile: agenda mensile/settimanale; anagrafiche professionisti; scheda di Alice/Pietro con lo stesso intestatario Laura; 17 righe raggruppate nel Report cliente; sedute chiuse, parzialmente incassate, non incassate, annullate e future; assenza di importi addebitati per colloqui gratuiti; posizioni economiche e CSV.

**Flusso «Nuovo paziente» della presentazione:** questa PR aggiunge una modalità specifica per lo STAGING sintetico configurato esplicitamente con `cc_presentation_intake=1`, `cc_presentation_site` corrispondente al sito, `cc_synthetic_dev=1`, `mute_emails=1`, invii Healthcare disabilitati. Soltanto con tutte le condizioni attive il form mostra nomi leggibili senza UID o avvisi tecnici e il backend genera l'identificativo interno. L'inserimento di telefoni/email reali e identificativi fiscali reali resta vietato; le preferenze TS non attivano trasmissioni. Verificare col clone reale e test browser prima di abilitare sullo STAGING. Se il flag non è attivo, il precedente flusso tecnico resta in vigore senza rilassamenti.

**L'opzione di inserimento leggibile non autorizza l'inserimento di dati personali reali:** per nuovi pazienti manuali del cliente servono dati inventati, senza recapiti recapitabili. Disattivare `cc_presentation_intake` al termine della presentazione o prima di un qualsiasi ingresso operativo con dati reali, da pianificare separatamente con protezioni appropriate.

**Non dichiarare STAGING popolato** senza prova di `inspect` dal sito e riscontri browser.
