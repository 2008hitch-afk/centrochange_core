# Centro Change — percorso demo cliente

**Ambiente:** unico DEV sintetico `centrochange-dev`. La presentazione si svolge inizialmente tramite condivisione schermo dell'Owner. Nessun accesso diretto del cliente, dato reale, pagamento esterno, email reale o invio fiscale reale è previsto.

## Accesso dell'Owner

Nella propria sessione SSH: `ssh -N -L 8082:127.0.0.1:8082 empv26@srv2033673`. Aprire `http://127.0.0.1:8082/app/cc-unified-desk?cc_view=agenda` nel browser. Usare le credenziali demo già consegnate tramite canale privato. Non inserire password nella guida, nella chat della presentazione o in GitHub.

## Sequenza consigliata

Usare i record dimostrativi leggibili Alfa, Beta, Gamma e Theta; non presentare le fatture di prova `CC-MVP-POS-*` annullate come operazioni del cliente. Prima di ogni modifica, verificare che il record sia sintetico e che l'azione sia reversibile; in caso contrario mostrare la prova precedente e il risultato corrente in sola lettura.

| Passo | Ruolo | Mostrare | Risultato da spiegare |
|---|---|---|---|
| 1 | Direzione | Login → Agenda | Agenda iniziale, disponibilità e filtro professionisti. |
| 2 | Segreteria | Ricerca e anagrafica pazienti | Ricerca autorizzata, profilo e assegnazione nel perimetro dei permessi. |
| 3 | Direzione | Professionisti e Disponibilità | Anagrafica separata da calendario e accessi operativi. |
| 4 | Segreteria | Agenda → Prenota, sposta, cancella | Stato seduta, collisioni e motivi; usare solo fixture nuova, identificabile e reversibile. |
| 5 | Professionista Alfa | Seduta, nota e storico | Nota riservata, chiusura, revisione e audit; Beta/C non vedono dati non assegnati. |
| 6 | Direzione | Servizi, Tariffe, Modelli pacchetto | Catalogo e prezzi canonici; nessun prezzo inventato nella presentazione. |
| 7 | Finance | Fatture pazienti → Incassi e pagamenti | Stato documento, pagamento carta/POS simulato via ERPNext, saldo e collegamento; usare l'evidenza sintetica precedente o una nuova fixture controllata. |
| 8 | Finance | Movimenti bancari → Banca | Movimento, importo residuo e riconciliazione tracciabile. |
| 9 | Finance / Commercialista | Allegato amministrativo | File privato associato al documento, lettura autorizzata e diniego al Professionista. |
| 10 | Finance / Commercialista | Report professionisti, economico pazienti, Libro giornale e Bilancio di verifica | Filtri di periodo/centro, risultati e CSV in italiano. |
| 11 | Finance | SdI e TS simulati | Stati e problemi leggibili; nessuna trasmissione reale. |
| 12 | Direzione | Gestione accessi → Registro modifiche | Ruoli, audit e controlli server-side; mostrare una prova preesistente per revoche mutative. |

## Validazione cliente

Per ogni passo chiedere: l'operatore trova la funzione, capisce cosa vede, sa quale azione è consentita, riconosce il risultato e considera comprensibili lingua/date/orari? Annotare `ACCETTATO`, `OSSERVAZIONE` oppure `CORREZIONE RICHIESTA`, ruolo, pagina, scenario, comportamento atteso/osservato, screenshot e priorità. Registrare separatamente giudizi funzionali e visivi. L'Owner raccoglie una decisione esplicita; nessun PASS tecnico equivale all'accettazione cliente.

## Limiti da dichiarare

- DEV privato con dati sintetici; Centro A operativo, Centro B inattivo. Nessuna produzione o conformità fiscale dimostrata.
- SdI, TS, notifiche esterne e carta/POS non contattano provider reali.
- Le fatture tecniche di prova annullate restano nello storico contabile per tracciabilità.
- La review visiva della sidebar e delle liste native è ancora aperta; vedere il [rapporto demo](../evidence/client-demo/CENTROCHANGE-CLIENT-DEMO-READINESS-REPORT-2026-10-19.md).
- Accesso diretto del cliente richiede una decisione separata su rete, isolamento e consegna sicura delle credenziali.
