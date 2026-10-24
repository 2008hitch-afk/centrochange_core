# AUDIT-05 — Professionisti e accessi

Issue [#171](https://github.com/2008hitch-afk/centrochange_core/issues/171). Baseline `main` `61324c8f462a07aa1b893c69a52e825e4342f9db`. Questo documento è l'oracle del candidato; i risultati Frappe/DEV e la decisione Owner sono registrati nella PR e nella Issue, senza attribuire PASS live ai mock.

| Requisito | UI Premium | API / dato canonico | Positivo | Negativo / limite | Stato al commit |
|---|---|---|---|---|---|
| CC-CAP-002 e CC-EXT-004: identità, stato, lista, ricerca, scheda | `#Professionisti`, `Professionals` | `profiles.practitioners`, `profiles.practitioner_detail`; Healthcare Practitioner, User, CC Center Membership | Nome/cognome, stato, pagina successiva e dettaglio nel centro operativo | Centro diverso/inattivo, record altrui, 403, lista vuota, ricerca oltre bootstrap e risposta tardiva | Offline PASS; clone/DEV da verificare |
| CC-EXT-009: modifica autorizzata | `#Archivi` → Professionisti, `ScopedArchive` | `profiles.practitioner_save`; first_name/last_name; Version e CC Audit Event | Manager: motivo, nuova versione, persistenza e replay stessa chiave | Segreteria/professionista/Guest, stale, chiave diversa, campo extra, CSRF, IDOR | Offline PARTIAL; scritture solo clone |
| CC-CAP-005/033/038/039 e CC-EXT-020/026/027 nel perimetro | Menu, URL, scheda, ricerca, Agenda/selettore/Report | DocType permission hooks, membership attiva, Branch operativo, practitioner_for | Professionista proprio; Manager nel centro autorizzato; Segreteria directory limitata | Revoca e centro inattivo negano DocType/query/API; centro B isolato; nessun dato contabile | Offline PARTIAL; sette ruoli+Guest clone/DEV da verificare |
| Regressioni mirate CC-CAP-004/007 | Pazienti assegnati, Agenda, Disponibilità | Assegnazioni/Marley esistenti | ID canonici coerenti tra sezioni | Nessun edit esteso o permesso aggiuntivo | NOT_TESTED live |

Le catture in `docs/evidence/issue-171/` usano **API sintetiche mock** e dimostrano solo resa desktop/mobile. Il gate DEV richiede CI sullo SHA esatto, revisione indipendente senza Critical/Important, immagine/manifest coerenti, nuovo checkpoint cifrato, restore isolato PASS, test Frappe/MariaDB sul clone, fingerprint e rollback. `cc_premium_primary=1` resta invariato. Nessuna migration, modifica di ruoli/schema o scrittura UAT sul DEV.

## Difetti confermati e correzioni nel candidato

- La ricerca iniziale filtrava solo lo snapshot `bootstrap`: ora interroga la lista Frappe paginata con ricerca server-side, loading, errore, stato e pagina vuota. Le risposte tardive di una pagina precedente non contaminano la ricerca corrente.
- Il permesso diretto del professionista restava valido con membership revocata o centro non operativo: query e controllo record ora richiedono identità attiva e almeno un'appartenenza a sede operativa. Le API scoped richiedono inoltre il centro operativo specifico.
- La scheda e l'Archivio mostravano il nome tecnico di una fixture HTTP, e il selettore Report usava una proiezione diversa: la lettura usa la stessa identità sintetica leggibile, mentre form e API mantengono i valori canonici. L'Archivio non ripete il titolo nel drawer.
- Nessun editor duplicato in `#Professionisti`: la modifica resta in `#Archivi → Professionisti`, con i soli campi già approvati `first_name` e `last_name`.
