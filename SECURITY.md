# Security Boundaries — Centro Change

## Obiettivo

Definire i vincoli tecnici minimi che ogni implementazione deve rispettare. Questo documento non costituisce certificazione o dichiarazione di compliance GDPR.

## Dati e ambienti

- DEV e test: solo dati sintetici o esplicitamente sanitizzati.
- Nessun dato cliente reale nel repository.
- Nessun backup, dump DB, private file o runtime state in Git.
- Nessun secret, password, token, API key o `.env` sensibile in Git.
- Staging/production devono avere configurazioni e storage separati.

## Autorizzazioni

I permessi sensibili devono essere applicati server-side.

In particolare devono essere testati:

- accesso professionista solo a pazienti assegnati;
- perdita accesso operativo dopo riassegnazione;
- segreteria senza accesso alle note professionali riservate;
- report/export/API coerenti con i permessi UI;
- audit completo non accessibile ai professionisti;
- sblocco chiusure automatiche solo ai ruoli autorizzati.

Nascondere campi, pulsanti o route lato client non è una misura sufficiente.

## Note riservate

`CC Organizational Note` e `CC Professional Note` devono restare entità separate salvo decisione architetturale successiva supportata da test equivalenti o migliori.

I test devono tentare esplicitamente leakage tramite:

- API REST;
- URL diretto;
- List View;
- Report;
- export;
- query custom;
- permessi dopo riassegnazione.

## Integrità dati

Funzioni critiche devono essere concurrency-safe e idempotenti quando applicabile:

- booking slot;
- spostamento appuntamento;
- consumo pacchetto;
- scheduler 21:00 / 07:00;
- reminder email;
- correzioni settlement;
- migrazioni.

## Upstream

- Vietate modifiche dirette al core Frappe/ERPNext/Builder senza decisione esplicita.
- Preferire hooks, override supportati, custom DocTypes, fixtures, migrations e API pubbliche.
- Aggiornamenti di versione richiedono test di migrazione e regressione.

## Networking e secrets

Per development locale:

- esporre servizi solo su localhost quando non serve accesso LAN;
- non pubblicare MariaDB/Redis direttamente sull'host se non necessario;
- mantenere secret in file esterni a Git con permessi restrittivi;
- usare porte e network isolate per `centrochange-dev`.

## Backup

Prima di dati reali richiedere:

- backup DB;
- public/private files;
- configurazione necessaria al restore;
- copia remota protetta;
- restore testato su ambiente isolato;
- procedura documentata;
- monitoring di scheduler/queue/email.

Un backup non testato non viene considerato strategia di recovery validata.

## Segnalazione

Qualsiasi rischio di leakage, perdita dati, accesso non autorizzato o semantica finanziaria errata deve bloccare il merge finché non è risolto o accettato esplicitamente come rischio residuo.