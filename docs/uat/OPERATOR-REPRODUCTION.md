# Riproduzione operatore — GOAL-02

Solo DEV `centrochange-dev` / `centrochange.local`, input sintetici; recipe Docker, pin e setup nativi del GOAL-01 accettato vengono riusati. Il [manifest](UAT-CANDIDATE.json) distingue commit sorgente, image ID, versione demo e hash semantico. Non implica merge dello stack.

## Build immutabile

Dal repository, con accesso Docker (se necessario `sg docker -c '…'`), eseguire:

```sh
python3 infra/uat_candidate.py --source-ref COMMIT_DEL_MANIFEST --name NUOVO_NOME_CANDIDATE --env-file /percorso/esterno/runtime.env
python3 infra/image_acceptance.py --source-ref COMMIT_DEL_MANIFEST
python3 infra/upstream_acceptance.py
```

Il nome ha forma `goal02-YYYYMMDD-rcN`. Il tool rifiuta di sovrascrivere un nome già esistente. Costruisce da `git archive` del commit esplicito, senza file locali non tracciati, credenziali o overlay; non modifica core upstream e non distrugge volumi. La configurazione riusa topology e volumi DEV accettati, migra tramite configuratore versionato. I sei servizi app condividono la stessa image. Le date e la configurazione dimostrativa sono fisse; non adattarle silenziosamente.

Prima di una critical regression la demo persistente deve essere assente: le suite storiche creano fixture isolate e alcuni test verificano site vuoto/assenza di documenti contabili preesistenti. Questa è una precondizione esplicita, non un indebolimento dei test.

```sh
docker exec centrochange-dev-backend-1 bench --site centrochange.local set-config cc_uat_demo 1
python3 infra/uat_demo.py reset
python3 infra/runtime_acceptance.py --env-file /percorso/esterno/runtime.env --snapshot /tmp/cc-uat-runtime.json
python3 infra/integrated_acceptance.py --env-file /percorso/esterno/runtime.env --output-dir /tmp/cc-uat-critical
python3 infra/finance_browser_acceptance.py --env-file /percorso/esterno/runtime.env --script threshold --output-dir /tmp/cc-uat-threshold
```

`reset` opera solo sul tag UAT esatto con controlli di ownership; rifiuta job contatto/fiscali ancora pendenti. Prima di un reset interrompere l’attività degli account demo e attendere i worker. Non applicarlo a un altro progetto/site o a dati reali. Nessun `down --volumes` è necessario per questo goal: il fresh build/recreate della fondazione accettata è evidenza riusata, non ripetuta senza motivo.

## Demo e verifica

```sh
python3 infra/uat_demo.py seed
python3 infra/uat_demo.py validate
python3 infra/uat_demo.py inspect
docker exec centrochange-dev-backend-1 bench --site centrochange.local execute centrochange_core.uat.acceptance.run
python3 infra/uat_browser_acceptance.py --output-dir /tmp/cc-uat-browser
```

Il seed è privato, non whitelisted: Administrator + `cc_synthetic_dev=1` + `cc_uat_demo=1`, lock tra processi, servizi nativi/prodotto e commit finale. Gli appuntamenti storici usano un clock locale al preparatore; gli applicativi continuano a usare l’ora reale. I servizi ordinari di prenotazione/chiusura/cancellazione mantengono validazioni e guardie prodotto. La creazione dei master sintetici riusa i helper interni autorizzati per Administrator, inclusi gli insert nativi con `ignore_permissions=True`; non è un’autorizzazione per gli utenti UAT o per il runtime operativo. Retry del seed conserva le modifiche cliente e restituisce replay; la verifica dello stato iniziale è un’azione separata. Un seed interrotto/incompleto richiede un reset esplicito, non un repair silenzioso.

`validate` attende gli esiti dei worker; restituisce PASS solo sullo stato iniziale atteso. Seriali, timestamp e password non entrano nell’hash semantico. Non confondere hash semantico e hash immutabile del codice/image. `--exercise` sul browser prova anche il differimento: modifica Theta e richiede reset/reseed prima della consegna.

Per dimostrare riproducibilità: salva i due output di `validate` fuori Git, esegui reset→seed→validate e confronta `semantic_sha256`; controlla che i nomi seriali siano nuovi senza includerli nell’hash. Il runtime finale deve restare con seed iniziale PASS dopo le prove modificative.

## Consegna account sintetici

```sh
python3 infra/uat_demo.py handoff --credentials-file /percorso/esterno/account-demo.json
```

File **0600 fuori Git**, contiene soltanto utenti/password generati per il DEV. Non stampare il contenuto nei log, in issue/PR, screenshot o report. Consegna al singolo validatore solo l’account necessario tramite canale autorizzato. Nessun invio email/Slack automatico è parte di questa procedura. Il tool browser usa un file temporaneo montato read-only e lo elimina sempre; non pubblica credenziali via website/RPC.

I dati nuovi della guida mantengono nome/UID col prefisso UAT. Dati creati fuori da quel prefisso rimangono fuori dal reset conservativo. Se i prerequisiti di site vuoto non sono soddisfatti, investigare l’ownership; non ampliare la cancellazione.
