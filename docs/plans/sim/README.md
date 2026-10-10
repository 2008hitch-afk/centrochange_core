# Simulazioni videocitofono Centro Change

**Stato: solo design / demo statica.** Nessun accesso a dispositivi fisici, dati del gestionale, pazienti, registrazioni, Wi-Fi, microfono o notifiche di sistema.

## Nuova demo — vista professionista e citofonata

Aprire [centrochange-professionista-intercom-demo.html](centrochange-professionista-intercom-demo.html) dal branch `plan/intercom-software-simulation-20261009`, usare **Download raw file** e aprire il file HTML sul PC o sullo smartphone. Su GitHub privato è necessario essere autenticati per scaricarlo. La demo **non è pubblicata su GitHub Pages**; non condividere una URL pubblica prima della review e dell'autorizzazione alla pubblicazione.

L'interfaccia è un mock coerente con il sistema grafico Centro Change approvato l'08-10-2026 (Tabler-inspired, brand testuale, primary teal `#12665F`). Non è una copia dei componenti runtime Tabler 1.6.1: la simulazione è intenzionalmente un unico file HTML senza dipendenze o CDN. Le voci Agenda, Pazienti e Disponibilità sono abbozzate con dati inventati; non rappresentano schermate cliniche reali.

### Walkthrough suggerito

1. In **Agenda** selezionare un professionista demo e osservare l'area di lavoro.
2. Cliccare **Simula campanello**: il citofono fisico risulta in squillo, la webapp mostra un avviso ai professionisti marcati presenti.
3. Cliccare **Visualizza** e **Rispondi e parla** dal profilo Alfa; lo squillo del citofono fisico si interrompe nel mock.
4. Cambiare profilo in Beta: l'audio è assegnato ad Alfa, ma Beta può comunque azionare **Apri porta** se presente e autorizzato. L'apertura è simulata.
5. Premere **Azzera scenario**, simulare il campanello e quindi **Risposta da citofono fisico**: la segnalazione sui telefoni scompare e la conversazione mobile non viene attivata.
6. Disattivare Wi-Fi/presenza o autorizzazione per vedere i controlli abilitati/disabilitati nella sola demo.
7. Su mobile verificare navigazione e layout responsive. Nessuna notifica nativa/Web Push è realmente inviata.

**Regole funzionali rappresentate:** primo professionista che risponde ha audio esclusivo; tutti i presenti e autorizzati possono aprire manualmente; il citofono fisico mantiene fallback; risposta sul dispositivo fisico interrompe gli avvisi cellulari; risposta mobile interrompe squillo fisico. Tutti questi comportamenti sono **richiesti**, non verificati su Comelit o garantiti su sistemi operativi reali.

## Vecchia simulazione

L'originale [intercom-demo.html](intercom-demo.html) resta disponibile come semplice simulatore standalone del videocitofono con credenziali finte **demo/demo**; non è la nuova demo integrata nella vista professionista.

## Notifiche Web Push nella V1 — requisiti non implementati dalla demo

Il cliente accetta **notifiche standard a schermo bloccato**, non una suoneria tipo telefonata in V1. Serviranno HTTPS, un backend di invio Web Push, service worker, permesso esplicito dell'utente e collaudo su iPhone/Android; per iPhone l'utente dovrà installare la webapp sulla schermata Home. La pagina non deve rimanere aperta, ma la consegna puntuale non è garantita: connettività, permessi e impostazioni Focus/risparmio energetico influenzano la disponibilità. La presenza Wi-Fi server-side resta una dipendenza diversa dai Web Push. La rimozione delle notifiche già presentate dopo la risposta su un altro dispositivo può avere limiti specifici di piattaforma: distinguere **stato chiamata aggiornato lato server** da **notifica OS già consegnata**.

Un'app nativa iOS/Android per un'esperienza chiamata avanzata è solo **possibile upselling futuro**, non inclusa nella V1. Anche in app nativa occorrerà verificare i comportamenti effettivamente disponibili nei due sistemi.

## Confini e autorizzazioni

- Solo dati sintetici. Nessuna credenziale vera, dato paziente o accesso di rete.
- Nessuna apertura automatica. Pulsante Apri solo simulato.
- Zero audio/video live, zero registrazione, zero storico reale.
- **Non** testare l'impianto Comelit attraverso questa pagina.
- Integrazione gestionale, push reali, rete, Comelit, POC e server richiedono gate e incarichi specifici; questa PR non li autorizza.
- Nessuna demo pubblica è stata deployata. Un link GitHub `blob` non si comporta come una webapp visitabile: prima della consegna al cliente servirà decidere hosting accessibile e privacy.

Per la tecnica, vedere il [masterplan](../VIDEOCITOFONO-SOFTWARE-MASTERPLAN-2026-10-09.md) e l'[handoff Codex](../VIDEOCITOFONO-CODEX-HANDOFF-2026-10-09.md).
