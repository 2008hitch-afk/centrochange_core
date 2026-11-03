# Protocollo EMPV — UAT funzionale e visuale automatizzato per GOAL

**Versione:** v1.1 · **Ambito:** FEATURE / MAINTENANCE con webapp e backend · **Stato:** protocollo metodologico approvato dai Founder come parte della SOP v1.1; il motore tecnico resta `CANDIDATE_UNDER_VALIDATION` e non è un orchestratore operativo di deploy.

## Risultato promesso
Consegnare una funzione verificata rispetto ai **requisiti e alle decisioni approvate del committente**, non soltanto rispetto al codice scritto e ai test creati dallo stesso agente. Una sola consegna per GOAL, niente walkthrough a micropassaggi per Owner. L'Owner mantiene la decisione finale su UX, risultato commerciale, merge e produzione.

## Oracle di accettazione indipendente (prima di implementare)
- Creare una matrice `requirement_id / decisione vigente → azione utente → ruolo e centro → effetto atteso UI → API/backend/DocType → scenario positivo e negativo → evidenza`, con URL/riferimento alla fonte cliente.
- Preservare gli stati APPROVATO, DEFERRED, ESCLUSO e NOT_TESTED della fonte; non trasformare richieste in proposta in requisiti obbligatori.
- Preparare i criteri **prima** del codice, oppure farli riesaminare da un reviewer indipendente dalle modifiche. Vietato modificare criteri attesi per far passare un'implementazione difettosa senza registrare una decisione Owner.

## Esecuzione automatica reale (Codex, nel medesimo GOAL)
1. Build/CI, unit e integrazione, typecheck/manifest; test deterministici positivi, negativi, bordo e regressione, dati e orari inclusi.
2. Con **gate DEV esplicito e condizionato** nello stesso GOAL: preflight, backup cifrato, restore isolato e rollback disponibile; installare solo risorse e servizi autorizzati. Senza quel gate operare solo su risorse isolate e chiedere un'unica decisione DEV raggruppata.
3. UAT di simulazione cliente con browser reale (Playwright o equivalente) **e API/backend reali**: click, form, salvataggio, refresh, errori e riprova, route diretta, login/logout, ruoli e segregazione centro; verificare persistenza e risultati server, non solo toast o status HTTP.
4. Mutazioni soltanto su fixture sintetiche con ID/ownership certi, checkpoint e teardown/rollback verificati; non creare/modificare utenti, pazienti, fatture o appuntamenti preesistenti per comodità dei test.
5. Prove desktop e mobile: screenshot **sanitizzati**, focus/tastiera, responsive e overflow, testi in lingua, nomi leggibili, stati vuoti, layout/azioni accessibili. La comparazione visiva automatica è **evidenza tecnica**, non approvazione estetica del cliente. È ammesso proporre 2–3 schermate salienti all'Owner anziché farlo cliccare ovunque.
6. Se emerge un difetto ordinario nel perimetro: **FIX → RETEST → CI → DEV controllato se autorizzato → LIVE UAT** senza un nuovo micro-mandato. Ogni nuovo SHA richiede gate tecnici e fingerprint rinnovati; rischi materiali o scope nuovo richiedono nuova decisione Owner.

## Copertura UAT di TUTTE le interfacce nel Goal

Il Goal deve elencare **ogni interfaccia/route o flusso utente modificato**, ricavandolo da requisiti approvati e modifiche effettive. Codex controlla ciascuno con browser, API/backend, operazioni positive e negative, permessi, salvataggio e persistenza, error/empty/loading, responsive desktop/mobile, focus/tastiera, accessibilità e regressioni pertinenti. Non è sufficiente collaudare una pagina campione. Ogni interfaccia avrà nel report unico uno stato esplicito `PASS_OFFLINE`, `PASS_LIVE`, `FAIL`, `BLOCKED` o `NOT_TESTED`, evidenza e screenshot sanificati collegati a commit e ambiente. Il reviewer indipendente verifica che nessuna interfaccia sia stata esclusa per ottenere il PASS.

**Autonomia Codex:** esegue test, corregge difetti e ritesta interamente nel medesimo Goal, senza richiedere nuovi micro-mandati. Il controllo finale di voi Founder riguarda **ogni interfaccia**, presentata in un'unica sessione conclusiva (eventualmente con un elenco di correzioni). Non approvate ogni clic o passaggio tecnico. `READY_FOR_REVIEW` significa che Codex e reviewer hanno terminato il pre-UAT; `OWNER_ACCEPTED` richiede un riscontro umano separato per le interfacce interessate. Il solo JSON non autentica approvazioni o test reali.

## Report di accettazione e stati non falsificabili
Una matrice di risultato per requisito/scenario/ruolo/centro/device con `PASS_OFFLINE`, `PASS_LIVE`, `FAIL`, `BLOCKED`, `NOT_TESTED`, evidenza, ambiente+SHA, causa e limitazione. Distinguere test browser con API simulate da test Frappe reali. Snapshot/screenshot e log privati fuori da GitHub se contengono dettagli personali o segreti; pubblicare solo risultati sanitizzati.

Nessuna funzione è `PASS_LIVE` senza scenario osservato su backend reale; nessuna funzione è `OWNER_ACCEPTED` per decisione unilaterale di Codex. Un reviewer indipendente confronta matrice, codice e prove; Owner decide il pass finale tramite rapporto unico e una breve anteprima di schermate rappresentative, potendo richiedere un approfondimento solo su punti controversi.

**Mai impliciti:** merge PR, produzione, cutover, modifica schema/permessi, dati reali, spesa o ampliamento delle autorizzazioni DEV. Se manca un prerequisito il report rimane PARTIAL/BLOCKED, non PASS.
