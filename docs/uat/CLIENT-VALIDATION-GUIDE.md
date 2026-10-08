# Client Validation Guide — GOAL-02

Ambiente DEV con dati inventati, dataset `goal02-demo-v1`. Entrata: `/validazione`, con login personale del ruolo demo. Le password vengono consegnate separatamente dall’operatore; non sono presenti in questo documento o nel repository. Nessun invio reale, produzione o dato cliente/paziente reale è autorizzato.

La guida presente nell’app propone le prove pertinenti al ruolo e i collegamenti ad Agenda e Finanza. Non occorrono terminale, API, nomi di moduli o istruzioni tecniche per eseguire le prove operative. Le verifiche tecniche di accesso diretto sono nel pacchetto evidenze.

## Prima della prova

1. L’operatore consegna URL DEV raggiungibile e account sintetico; la build candidata è identificata dal [manifest](UAT-CANDIDATE.json). La consegna su rete cliente non è una pubblicazione autorizzata: questo runtime è locale.
2. Accedi a `/validazione`. Usa il ruolo indicato dallo scenario. Il suffisso account `a` indica professionista Alfa, `b` professionista Beta, `c` professionista senza anagrafica, `s` segreteria, `f` amministrazione, `t` commercialista, `m` direzione. Tutti gli account demo hanno dominio `example.invalid` e prefisso `cc-http-uat0000001-`.
3. Centro `CC-HTTP-UAT0000001 A` contiene il dataset. Il Centro B verifica la separazione degli accessi. I pazienti si riconoscono dal nome finale Alfa/Beta/Gamma/Delta/Epsilon/Zeta/Theta; il prefisso identifica dati inventati.
4. Agenda: Dal **28/09/2026**, Al **12/10/2026**, Aggiorna. Finanza: Dal **28/09/2026**, Al **31/10/2026**. Le date dello storico sono fisse; la prenotazione usa l’ora reale e richiede una data futura dal lunedì al venerdì, fra 09:00 e 16:00, per una seduta di 60 minuti.
5. Per una ripetizione indipendente di prove che modificano dati, chiedi il ripristino all’operatore. **UAT-04 e UAT-05 usano ripristini separati**: il movimento Beta da 60 deve essere provato con residuo iniziale 60.

I 100 EUR del servizio, 40 EUR del compenso e N=1 sono esclusivamente valori dimostrativi espliciti, non tariffe o soglie reali approvate per il cliente. Zeta ha intenzionalmente regola/soglia mancanti. Lo storico è preparato con orologio sintetico confinato al preparatore; non rappresenta servizi realmente erogati. Dopo il caricamento nessun orologio artificiale resta nel runtime.

## Scenari e risultati attesi

| Codice / ruolo | Passaggi nell’interfaccia | Risultato atteso |
|---|---|---|
| UAT-01 / professionista a o segreteria | Agenda, Alfa, + Prenota; seleziona professionista a, servizio demo, futuro intervallo libero e motivo. Ripeti sullo stesso intervallo. | Una sola nuova seduta, 60 minuti, 100 EUR; conflitto rifiutato senza alterare la prima seduta. Il prezzo registrato non cambia con modifiche successive della tariffa. |
| UAT-02 / professionista a | Apri storico Delta e confronta le due cancellazioni; apri Epsilon. Annulla la nuova prenotazione UAT-01 con almeno 48 ore di preavviso. | Delta a 48h puntuale/non dovuta, a 47h tardiva/dovuta. Epsilon coperta da pacchetto, una unità consumata. Nuova cancellazione puntuale senza debito, storico conservato. |
| UAT-03 / a, b, c, s | a: Alfa → Note; b: agenda e pazienti; c: agenda; s: Alfa → Note. | a vede la propria nota privata; b vede Zeta, non Alfa; c non vede dati pazienti/sedute; s vede note organizzative ma nessun contenuto privato. Centro B non compare ai ruoli limitati ad A. |
| UAT-04 / f o s | Finanza → Fatture pazienti → Beta → Registra pagamento 20 EUR, motivo. Gamma e Alfa bozza per confronto. | Beta residuo 60→40; Gamma zero; Alfa bozza senza contabilizzazione. L’incasso contabile non riscrive il prezzo storico o il fatto operativo Paid/Unpaid. |
| UAT-05 / f, ripristino iniziale | Banca → movimento 60 con riferimento Beta → Scegli documento → Beta → motivo. Poi Fatture fornitori → residuo 100 → Registra pagamento 30. | Abbinamento suggerito Beta, riconciliazione esplicita: residuo Beta e movimento non allocato zero. Movimento 999 senza abbinamento. Fattura fornitore residuo 100→70. |
| UAT-06 / f e m | Professionisti → Alfa → posizioni. m: Configura soglia non incassate e Riconosci compenso sospeso, con motivo. | Prima Alfa 40 EUR confermati, seconda sospesa/importo da definire con N1. Zeta in revisione per configurazione mancante. Solo m cambia soglia/override; storico originario e audit conservati. |
| UAT-07 / f, m | SdI e TS → Gamma; TS → Beta. Leggi dettaglio e tentativi. m può creare versione rivista TS con input esclusivamente sintetici. | Esiti simulati separati; Gamma accettata, Beta eligibilità da verificare. Nessun invio reale; nessuna inferenza automatica da SdI a TS. |
| UAT-08 / f, t, m | Riepilogo → confronta fatture e residui → Esporta CSV; t consulta fatture; m apre Registro modifiche e Gestione accessi. | Totali coerenti con i documenti nativi; CSV senza note private; t sola lettura; audit con autore/data/motivo, gestione accessi riservata alla direzione. |
| UAT-09 / visitatore anonimo | `/primo_incontro`: route Marco, slot futuro disponibile, nome `CC-HTTP-UAT0000001 Invitato`, cognome `Demo`, email `cc-http-uat0000001-invitato@example.invalid`, sesso e conferma. | Prima seduta creata una volta; nessun elenco pazienti esposto. Email reale e input non validi sono rifiutati nel DEV. Segreteria vede la nuova identità/seduta. Il prefisso mantiene il dato nell’area ripristinabile. |
| UAT-10 / s | Pazienti → Nuovo paziente: nome `CC-HTTP-UAT0000001 Nuovo`, UID `CC-HTTP-UAT0000001-NUOVO`, sesso, professionista a e motivo. Apri storico. | Un Patient centrale con assegnazione esplicita; dati disponibili al solo contesto autorizzato. Ricerca per UID esatto richiede autorizzazione e una successiva assegnazione, non concede accesso implicito. |
| UAT-11 / s o m | Apri una seduta storica chiusa di Alfa; prova modifica ordinaria. Riapri con motivo, modifica/chiudi dove consentito e consulta storico/audit. | Modifica ordinaria della chiusa rifiutata; correzione esplicita autorizzata e tracciata. Non segnare svolta una seduta futura: il server rifiuta. |
| UAT-12 / m | Finanza → Fatture pazienti: Alfa bozza → Approva e contabilizza; consulta residuo. Apri Theta: residuo 100 EUR, scadenza 30/09/2026 e prenotazione successiva bloccata. Premi Differisci scadenza con motivo e scegli una data futura che estenda la scadenza. | Bozza diventa documento nativo definitivo una volta; debito e nuova scadenza rimangono distinti. Gli insoluti scaduti bloccano la seduta successiva; il differimento motivato non cancella il debito. Theta deve passare a nessun blocco attuale; residuo 100 EUR e scadenza nativa originaria restano invariati. Il retry e il blocco della seduta successiva sono verificati anche automaticamente. |
| UAT-13 / f | XML ricevuti → sorgente classificata → originale privato; sorgente non valida → stato. Fatture fornitori → Annulla documento → Rettifica e riemetti con motivo, data e scadenza. | Originale immutabile e privato; input non valido senza contabilizzazione. Cancellazione/storno e nuova fattura collegata, originale conservato; scadenza della rettifica esplicita. |
| UAT-14 / f e m | Su una fattura paziente appena contabilizzata, SdI → prepara → Esegui tentativo simulato: errore temporaneo → aggiorna → nuovo tentativo accettato. Per TS prepara fonte/fattura; m rivede input sintetici e invia simulazione. | Tentativi e versioni conservati, errore recuperabile visibile, nessuna duplicazione contabile o traffico esterno. TS mantiene la verifica esplicita di opposizione/eligibilità. |
| UAT-15 / f | Professionisti → Confronta fattura ricevuta; scegli fattura nativa e snapshot attesi. Coda amministrativa → assegna responsabile/priorità/motivo. | Confronto esplicito contro fattura fornitore, incongruenza visibile; nessuna creazione automatica di debito dal solo atteso. Una condizione resta una sola su refresh/retry, con cronologia di gestione. |
| UAT-16 / m, poi a | Gestione accessi → revoca appartenenza di a ad A, motivo; accedi nuovamente come a. Ripristina con m. | Revoca effettiva sul server per lista, documento/API e workspace; ripristino esplicito. UI nascosta non è il controllo di sicurezza. |

I casi temporali esatti, concorrenza, retry/rollback, payload malformati, download protetti e API non autorizzate sono riprodotti dalla critical regression suite. Il cliente non deve manipolare orologi, container, sorgenti o database per validarli.

## Registro della validazione cliente

Usa una riga per scenario e per tentativo. Non confondere il PASS tecnico registrato nel pacchetto con l’accettazione cliente, che è **NOT_EXECUTED / da raccogliere**.

| Build | Scenario | Ruolo | Data | Atteso | Osservato | PASS/FAIL/BLOCKED | Evidenza sintetica / defect |
|---|---|---|---|---|---|---|---|
| candidate dal manifest | UAT-… | … | … | … | … | NOT_EXECUTED | … |

Una prova non eseguibile a causa di una limitazione nota va registrata BLOCKED con riferimento al [Known Limitations Register](KNOWN-LIMITATIONS.md). Errori tecnici vanno associati allo scenario e riprodotti nel DEV; decisioni business o fiscali restano alle autorità competenti.
