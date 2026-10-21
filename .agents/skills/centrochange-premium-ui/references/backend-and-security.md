# Frontend React → Frappe / ERPNext / Marley / centrochange_core

## Principio

Cambiare la vista **non cambia sistemi autorevoli né permessi**. No copia in DB frontend, no nuova source-of-truth, no business logic economica/clinica ricostruita nel browser.

## Contratti e guardie prima del coding

1. Leggere `AGENTS.md`, `ARCHITECTURE.md`, `SECURITY.md`, documentazione API ufficiale e implementazione effettiva delle versioni pinned.
2. Mappare endpoint → task → ruolo → DocType → campi/filtri → stato mutativo/read-only → paginazione → errori → audit → test.
3. Autenticazione/sesssione Frappe (cookie, CSRF, SameSite, CORS), routing same-origin, logout, route dirette, refresh e asset; verificare sul runtime pinnato prima di assumere compatibilità.
4. Positivi e negativi lato server per prenota/sposta/cancella/chiudi, note private, pacchetti, fatture, compensi, riconciliazione, centri attivi, export/print, Guest.
5. Non affidarsi a sola condizione UI o REST DocType generico: verificare `get_all`, endpoint diretti, query/list/report/export e scope di paziente, professionista, centro.
6. Search bounded, debouncing, niente risultati async stale, rate limits ove supportati.
7. No dati reali, credenziali, note riservate nei log browser, screenshot, analytics, codice o bundle.

## Localizzazione

- Testi umani `it-IT`, date `GG/MM/AAAA`, orari `HH:mm`, timezone `Europe/Rome`, Euro.
- API/integrazioni e audit mantengono formati tecnici/ISO quando prescritti.
- Errori backend → messaggi italiani contestuali, senza esporre stack trace/identificativi riservati.

## Confini

- ERPNext Desk nativo riservato eventualmente a tecnici autorizzati, non link involontari negli operatori Centro Change.
- Nessun DocType, schema, accounting, security, TS/SdI o business rule alterati materialmente senza gate esplicito.
- Solo fixture isolate con fingerprint/cleanup per mutazioni. No server clone, database o DEV shared changes dalla DECISION-061.
