# AUDIT-02 #161 — rifinitura delle etichette

**Perimetro:** PR #163, solo presentazione React e regressioni offline. Le sei prove di navigazione Owner già registrate in #161 restano valide. Questo intervento non aggiorna il DEV, non modifica la fixture A/B e non riapre gli audit funzionali Agenda/Pazienti.

## Diagnosi per fonte

| Punto visibile | Fonte e causa | Intervento |
|---|---|---|
| Centro nell'header | `workspace.bootstrap.centers` fornisce `Branch.name` e `Branch.branch`. Il precedente React usava solo `branch`: se il manifest UAT conosceva l'alias dell'ID, lo ignorava. Nella fixture Gate 2 il campo `branch` stesso contiene un codice tecnico: non esiste una denominazione configurata. | Priorità a alias esatto per ID, poi `branch` descrittivo. Per il codice sintetico con lettera esplicita si mostra `Centro di prova A/B`; altrimenti `Sede senza nome`. Il valore `<option>` resta l'ID canonico. Selettore mobile più largo, verificato a 390 px. |
| Professionisti in Agenda e selettori collegati | `workspace.bootstrap.practitioners` fornisce ID e `practitioner_name`, già filtrati per centro. React usava il solo nome snapshot e ignorava un eventuale alias esatto dell'ID. Nella fixture Gate 2 il nome è esso stesso tecnico; manca un nome/cognome umano nella fonte. | Resolver unico: alias esatto, nome configurato, `Professionista di prova B/C` soltanto per discriminatore sintetico esplicito, poi `Professionista senza nome`. Le righe, i form e le API conservano gli ID originali. |
| Ricerca e dettaglio Paziente | `patient_name` può essere un codice sintetico. La ricerca già usa l'API scoped `workspace.patient_search`; alcuni dettagli mostravano un'etichetta `Codice demo` e stati Frappe in inglese. L'alias del servizio di prova esiste nel manifest UAT ma non veniva applicato nello storico sedute. | Il resolver Patient preferisce l'alias esatto e usa un fallback di prova solo per ID sintetici riconosciuti. Tolta l'etichetta ridondante `Codice demo` dal pannello; applicati alias dei servizi e le traduzioni degli stati già usate dalla stampa Frappe. Nessuna modifica a note o fatti clinici. |
| Note organizzative e servizi della fixture Gate 2 | Ispezione **in sola lettura** del DEV: i contenuti delle note e alcuni snapshot servizio sono stati scritti letteralmente con codici sintetici; il campo autore contiene un account tecnico. Non risulta una descrizione affidabile alternativa per tali contenuti. | Testo, autore e riferimenti restano invariati per preservare audit e significato. Servono dati di prova descrittivi autorizzati per eliminarli dal DEV; nessun alias inventato o modifica live in questo intervento. |

`workspace.bootstrap` espone già i campi descrittivi necessari: **nessuna nuova API o modifica di permessi**. I resolver agiscono solo sulla presentazione. Il test Python controlla nomi, ID e separazione A/B; il test browser controlla valori delle `<option>`, righe Agenda, ricerca, dettaglio e assenza di pazienti del centro precedente.

## Evidenze offline

- Python `python3 -m unittest discover -s tests -p 'test_*.py' -q`: **52/52 PASS**.
- `npm run typecheck`, `npm run build`, `python3 infra/verify_full_single_stack.py --source`: **PASS**. Asset generati e manifest completo aggiornati insieme; il verificatore richiede il nome esatto del nuovo chunk Vite.
- Playwright sintetico `playwright.config.ts`: **102 PASS, 8 SKIP previsti per device**, nessun FAIL.
- Playwright scoped `playwright.scoped.config.ts`: **30/30 PASS**, nessun FAIL.
- Screenshot della build locale con fixture sintetiche: [Agenda A desktop](../evidence/issue-161/polish-agenda-a-desktop.png), [Agenda B desktop](../evidence/issue-161/polish-agenda-b-desktop.png), [Agenda B mobile](../evidence/issue-161/polish-agenda-b-mobile.png), [Paziente desktop](../evidence/issue-161/polish-patient-a-desktop.png), [Paziente mobile](../evidence/issue-161/polish-patient-a-mobile.png), [Centro B mobile](../evidence/issue-161/polish-center-b-mobile.png). Le immagini contengono solo dati di prova; sono state ispezionate a 1440×900 e 390×844. Le altre due varianti sono nella stessa directory.

**Limite:** Playwright intercetta le API. Questi PASS non validano la nuova build su Frappe reale. L'immagine e la fixture correnti sul DEV restano quelle del precedente Gate 2; l'Owner ha già registrato 6/6 gesti di navigazione PASS su quella versione. Il nuovo polish è `PASS_OFFLINE / NOT_TESTED_LIVE / OWNER_FINAL_VISUAL_UAT_PENDING`.

## Unico gate DEV successivo

Congelare SHA PR #163 e risultato GitHub Actions del medesimo commit. Costruire un'immagine completa con `infra/Dockerfile.single-stack-full`; confrontare source manifest, asset, versioni e ID immutabile. Prima di uno switch, rieseguire preflight del solo `centrochange-dev` (configurazione privata con identità autorizzata, Site/DB, dati sintetici, RAM/disco/cgroup/OOM e rollback), checkpoint cifrato integrale a sei componenti e restore reale isolato con confronto Site/DB e `PASS_RESTORE`. Solo con tutti i gate PASS, e con **nuova autorizzazione Owner specifica**, sostituire i sei servizi applicativi `backend`, `frontend`, `websocket`, `queue-short`, `queue-long`, `scheduler`; preservare MariaDB, due Redis, Site, DB, volumi, rete e porta. Nessun migrate, cambio permessi, reset o attivazione di `cc_premium_primary=1`. Verificare asset HTTP e 6/6 gesti Owner più etichette A/B, ricerca, dettaglio, desktop/mobile; mantenere immagine precedente e backup per rollback sicuro. L'attuale mandato di polish **non autorizza** questo switch.
