# Centro Change — traccia demo cliente, 5 novembre 2026

Durata indicativa 12–15 minuti. Ambiente: https://centro-uat.empv.it/premium; prenotazione pubblica: https://centro-uat.empv.it/primo_incontro. Usare soltanto l’account demo `cc-http-uat0000001-m@example.invalid` (ruolo Manager / Amministrazione-Direzione) e le anagrafiche sintetiche già autorizzate. Credenziali tramite canale riservato; non inserirle in questo documento.

## Prima della chiamata

- Aprire login e gestionale; controllare che sia selezionato Centro A. Il 4 novembre l'immagine installata era `cc75-ux:3cf75ab`; ricontrollare se l'ambiente cambia.
- Preparare l’Agenda su **Centro A, settimana 2–8 novembre 2026**. Sono stati creati e verificati quattro appuntamenti demo il 5 e il 6 novembre alle 09:00: Marco in sede e Francesca online, ciascuno in entrambi i giorni. È presente anche la prova sintetica separata del 5 novembre alle 09:20. Nella vista settimanale può sovrapporsi alla card Marco delle 09:00 e intercettarne il clic: per la demo preferire gli appuntamenti del 6 novembre. Le due righe dei professionisti possono richiedere scorrimento verticale. Se necessario, la settimana 28 settembre–4 ottobre contiene nove fixture precedenti.
- Tenere separata una scheda browser per il primo incontro pubblico. Non confermare operazioni durante la demo se non concordate e limitate a fixture sintetiche test-owned.

## Sequenza suggerita

1. **Accesso e Agenda — 3 min.** Accedere con l'account demo, mostrare Centro A, settimana e professionisti. Nella settimana corrente aprire una delle quattro card demo del 5 o 6 novembre alle 09:00 e mostrare dati operativi. Eventualmente aprire «Nuova prenotazione» senza confermare.
2. **Pazienti — 2 min.** Aprire Pazienti, cercare una delle anagrafiche demo e aprire la scheda. Mostrare i dati e le sezioni autorizzate, senza inserire dati personali reali. Nel profilo sintetico provato il campo Nome mostra il codice fixture e Cognome/Email sono vuoti: presentarlo esplicitamente come dato di prova.
3. **Professionisti, servizi e disponibilità — 2–3 min.** Aprire un professionista demo, la scheda di un servizio e la vista Disponibilità. Spiegare che listino e durata effettivi dipendono dal catalogo configurato.
4. **Report e primo incontro — 3 min.** Aprire Report: il collegamento diretto `#Dashboard` porta a Report; non presentarlo come dashboard autonoma. Poi nel sito pubblico scegliere sede oppure online, selezionare Marco oppure Francesca, cercare gli orari e arrivare alla schermata dati. Spiegare che il colloquio è gratuito, dura 20 minuti ed è l'unico appuntamento previsto dal percorso pubblico. Fermarsi prima della conferma, salvo mandato specifico su dati sintetici test-owned.
5. **Limiti e prossimi passi — 2–3 min.** Spiegare che il pagamento cumulativo/parziale e la rimozione del blocco per insoluti sono nel candidato isolato #203, non nell'UAT attuale. La seduta successiva da 45 min / 44 EUR è approvata, ma resta da configurare: non è disponibile nel catalogo UAT verificato. Fatture, riconciliazioni e trattamento fiscale richiedono la videocall dedicata.

## Stato del preflight del 4 novembre

- **UAT verificato:** login con account demo, shell e Agenda, card appuntamento di fixture, form nuova prenotazione aperto, pagina paziente sintetico, dettagli professionista e servizio, Disponibilità. Endpoint privati Guest negati (403). Pagina pubblica e disponibilità restituite per tutte e quattro le combinazioni sede/online × Marco/Francesca; schermata dati raggiunta per due combinazioni. Dopo autorizzazione Owner, quattro prenotazioni sintetiche sono state confermate sull’UAT tramite API, una per combinazione prevista in ciascun giorno; le quattro card sono state aperte nel browser e la disponibilità risulta aggiornata. Inoltre una prova browser Guest sull’UAT ha confermato e persistito una sola prenotazione sintetica (`HLC-APP-2026-00087`, 5 novembre 09:20), senza variazioni a code email/SMS o contabilità e senza alterare i record preesistenti. In un clone isolato della stessa immagine, due prenotazioni reali sintetiche (Marco/sede e Francesca/online) sono state confermate nel browser, persistite, aperte in Agenda e verificate senza duplicazioni, invii reali o variazioni contabili.
- **Solo clone/CI:** incassi #203, pagamenti parziali/multipli, no blocchi ordinari e controlli associati; CI PASS su `53660c4`. Review indipendente APPROVED pendente. Non presentare questi flussi come disponibili nell'UAT attuale.
- **Non pronto:** servizio successivo 45 min/44 EUR assente nel catalogo letto; fatturazione fiscale, storni/rimborsi e riconciliazione da definire. Su UAT `3cf75ab`, la posizione demo scaduta verificata risulta ancora bloccante: evitare di promettere nuove prenotazioni senza blocchi per insoluti.
- **Non verificato in questo preflight:** tutte le combinazioni nella conferma browser pubblica UAT, invio email reale, tutti i ruoli e tutti i dati, disponibilità di slot al momento della demo. I risultati sintetici non sono produzione né accettazione complessiva del cliente.

## Piano alternativo

Se le quattro fixture attuali non fossero disponibili, usare le nove fixture della settimana 28 settembre–4 ottobre. Se non ci sono slot pubblici, mostrare scelta modalità e direttore, poi spiegare che occorre scegliere un altro periodo; non promettere la conferma. Se manca l’account demo, interrompere la demo autenticata: non usare account personali o aggirare il login.

L’indirizzo `/primo-incontro` restituisce 404: usare esclusivamente `/primo_incontro` finché il fix non è rilasciato e verificato. Non presentare la seduta successiva 45/44 né gli incassi #203 come disponibili.

La [procedura fixture e pulizia](DEMO-2026-11-05-PROCEDURA-FIXTURE.md) documenta i quattro appuntamenti creati. L’eventuale cancellazione è solo logica, conserva lo storico e può lasciare le card visibili in Agenda; non eseguirla durante la demo.
