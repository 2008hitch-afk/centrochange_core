# Centro Change — checkpoint autorevole della fase attuale (26/10/2026)

## ULTIMO STATO VERIFICATO — CORE #173 DEV installato secondo rapporto AGY, UAT OWNER PENDING

**Checkpoint successivo al gate autorizzativo qui sotto (26/10/2026):**

- [Report AGY Issue #173 #6427998113](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6427998113), duplicato su [PR #175 #6427999519](https://github.com/2008hitch-afk/centrochange_core/pull/175#issuecomment-6427999519): stato comunicato **`DEV_INSTALLED_READY_FOR_OWNER_UAT`**.
- Identità codice verificata direttamente su GitHub: PR #175 `OPEN/DRAFT/UNMERGED`, SHA `d500fff45cc5ca70c5ef33575aac4e58d4fed505`; [CI #40396123393](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40396123393) `backend-offline` e `frontend-synthetic` **SUCCESS**. PR #172 e #174 anch'esse ancora `DRAFT/UNMERGED`. L'Owner ha già dato accettazione **scoped** #171, non ancora accettazione #173.
- **Dichiarato da AGY, non verificato direttamente dal revisore sul VPS:** tutti e 6 i container applicativi `centrochange-dev` usano `cc173-day-closure:d500fff` Image ID `sha256:8e9103aa301bf3da782e1882070de9d1518c07b908b12a775743eb93eb3cedd9`; DB/Redis invariati; fingerprint canonico prima/dopo `0f806a37849b571b213e71dcd5a7e6b6535a5bdb9314ca5c49fc2a536ed5e2ad`; 21/21 smoke tecnici, 6 screenshot DEV e rollback applicativo pronto.
- Backup cifrato e restore isolato dichiarati PASS nel rapporto. **Attenzione retention:** il backup `/tmp/cc-core173-backup/.../backup.tar.gpg` e le chiavi `/tmp/cc-core173-keys/` sono su percorso temporaneo; AGY deve verificarne la conservazione protetta fino al completamento UAT/rollback, senza pubblicare o esportare segreti, e prima della consegna definire retention secondo policy. Non dedurre protezione durevole dal solo flag AES-256 o chmod 0600.
- **Perimetro delle prove DEV:** lo smoke riportato dal tecnico ha consultato sedute di oggi e arretrate, inclusa `HLC-APP-2026-00024` del 14/10, ma afferma **ZERO mutazioni ai dati**. Quindi nessuna prova di `close_day` con salvataggio su record storici DEV e nessuna accettazione funzionale Owner. Le mutazioni + transazione/settlement/CSV sono provate sul **clone Frappe/MariaDB** come test tecnico, non dichiarare UAT mutativo DEV su storici.
- **Walkthrough Owner successivo:** accedere solo a [Premium DEV](https://centro-uat.empv.it/premium/) con account Professionista autorizzato, Agenda → «Chiudi la mia giornata» → giorno 14/10/2026 → leggere sedute arretrate, stato, data/ora, tariffa e POS, non confermare su sedute preesistenti; controllare in Direzione report/Agenda/visibilità e mobile. Per conferma persistente utilizzare **esclusivamente fixture sintetiche dedicate, reversibili, previo piano di cleanup**; altrimenti l'Owner effettua UAT visivo e il backend reale persistente rimane provato soltanto sul clone.
- **Gate:** `READY_FOR_OWNER_UAT_CORE173` (secondo rapporto AGY), **NON** `OWNER_ACCEPTED_CORE173`, `MERGED` o `PROD_DEPLOYED`. Non avviare successivi GOAL, non trasformare automaticamente requisiti Owner della matrice in PASS finché l'UAT conclusiva non è registrata. L'eventuale UAT Owner può esitare `PASS_SCOPED` o difetti mirati senza rifare #171.

---


## ULTIMO GATE OWNER — 26/10/2026 (prevale sulla fotografia precedente sotto)

**Owner ha risposto «Procediamo» alle due autorizzazioni distinte.**
- **AUDIT-05 #171: `OWNER_ACCEPTED_SCOPED_AUDIT05`** nel solo perimetro funzionale approvato, ufficializzato [su Issue #171](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6427680735). PR #172 resta DRAFT/UNMERGED; **MERGE NON AUTORIZZATO**. Non promuove a PASS funzionalità trasversali non provate e non comprende CORE #173.
- **CORE #173: `DEV_INSTALL_ALLOWED_CONDITIONAL`** nel SOLO `centrochange-dev`, annotato [su Issue #173](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6427702903). Candidato immutabile `d500fff45cc5ca70c5ef33575aac4e58d4fed505`, immagine `cc173-day-closure:d500fff`, Image ID atteso `sha256:8e9103aa301bf3da782e1882070de9d1518c07b908b12a775743eb93eb3cedd9`, CI `40396123393` SUCCESS. **Nessun deploy effettuato o autorizzato senza gate preflight**, backup completo cifrato, restore isolato, rollback e verifica baseline. Non autorizzati schema/ruoli/credenziali/dati storici/prod/merge.
- **Verifica GOAL #173:** PR #175 HEAD `d500fff`, DRAFT/UNMERGED, backend React e test Oracle reali/Chromium clone riportati PASS da AGY. `READY_FOR_DEV_GATE` ≠ `DEV_INSTALLED` ≠ `OWNER_ACCEPTED_CORE173`. Solo dopo installazione condizionata e UAT Owner dedicata quest'ultima potrà essere accettata.
- **Matrice CSV:** sempre **110 ID** e stati tecnici **12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED**. `Owner` aggiornato a `OWNER_ACCEPTED_FUNCTIONAL_LIMITED` per **soli 4 ID direttamente verificati #171** (`CC-CAP-002`, `CC-EXT-004`, `CC-EXT-009`, `CC-CAP-028`); nessuna accettazione per le altre capacità. Owner count ora **96 PENDING / 12 OWNER_ACCEPTED_FUNCTIONAL_LIMITED / 1 OWNER_ACCEPTED / 1 OWNER_APPROVED_DEV**. Ogni conteggio diverso riportato sotto rappresenta la **fotografia anteriore** alla decisione Owner.
- **Prossimo passo autorizzato:** AGY esegue in un ciclo il gate DEV #173 alle condizioni puntuali della Issue, oppure STOP/ROLLBACK; produce unico rapporto `DEV_INSTALLED_READY_FOR_OWNER_UAT` o `BLOCKED`, nessuna nuova area funzionale. La PR documentale #174 resta DRAFT, da integrare solo con autorizzazione separata e preservando la cronologia.

---

**Perimetro temporale e funzionale:**

**NOMI DA NON CONFONDERE:** in questo checkpoint «goal 5» dell'Owner significa **AUDIT-05 Professionisti, Issue #171**. Non significa il vecchio «GOAL-05 Delivery Closure» nominato nella roadmap MVP del 03/10: sono due numerazioni differenti. Il successivo lavoro *già richiesto* è **CORE #173**, non una delle fasi della roadmap storica.

 ricostruzione delle evidenze fino al 26/10/2026; include **AUDIT-05 Professionisti #171 / PR #172** e il requisito CORE **#173 «Chiudi la mia giornata»**, già approvato ma **non ancora attestato come implementato**. Gli altri GOAL, moduli o fasi successivi sono **ESCLUSI da questa valutazione**, anche quando alcune righe storiche dei 110 requisiti continuano a esistere nel CSV. Il documento non autorizza nuovi GOAL, merge, deploy, schema, policy o produzione.

> **Regola di precedenza:** le Issue/PR GitHub e il codice sulla SHA effettiva sono fonte autorevole dello stato dinamico. Questo checkpoint è una fotografia verificata; ogni agente deve aggiornare HEAD, CI, reviewer e DEV prima di operare. La matrice CSV conserva il significato originale di `Stato` **tecnico**, separato da `Owner`.

## 1. Percorso esatto della fase: non confondere i gate

| Oggetto | Stato verificato / fonte | Cosa non significa |
|---|---|---|
| AUDIT-03 Agenda, CC-EXT-003 | **OWNER_ACCEPTED** nel CSV tecnico/storico del percorso; non riaprire il walkthrough già superato | Non accetta nuovi flussi di chiusura |
| AUDIT-04 Pazienti [#167](https://github.com/2008hitch-afk/centrochange_core/issues/167) | **CLOSED / Owner accettato nel perimetro**; 8 righe `OWNER_ACCEPTED_FUNCTIONAL_LIMITED` | Non prova privacy/export globale di tutti i moduli |
| AUDIT-05 Professionisti [#171](https://github.com/2008hitch-afk/centrochange_core/issues/171) | **OPEN, in UAT finale; Owner acceptance formale NON registrata**, benchmark ultimo [rapporto](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6423949297) | Non equivale a GOAL chiuso |
| [PR #172](https://github.com/2008hitch-afk/centrochange_core/pull/172) | **OPEN/DRAFT/UNMERGED**, codice HEAD `a3e41a10287639a7c200992e45c3173b8ea33b46` | La CI verde non è merge, prod o Owner acceptance |
| [CI #40374937104](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40374937104) | GitHub Actions **SUCCESS**, job backend-offline e frontend-synthetic entrambi SUCCESS su `a3e41a1` | Non equivale ad API e scritture live DEV |
| DEV `https://centro-uat.empv.it/premium/` | AGY ha **documentato installazione** immagine `cc171-professionals:a3e41a1`, digest `sha256:6e338fa7d568152815ac990d1a895759087dd51d0f6ea5416463cdddaaed38d6`, restore isolato, 21/21 controlli tecnici e 11+3 screenshot; fingerprint DB pre/post uguale `0f806a37849b571b213e71dcd5a7e6b6535a5bdb9314ca5c49fc2a536ed5e2ad` | Evidenza **dichiarata dal rapporto AGY**, non accesso VPS indipendente del revisore ChatGPT |
| Reviewer #172 | Rapporto AGY dichiara **revisione indipendente PASS, 0 Critical/Important**; elenco review GitHub al checkpoint **vuoto** | Distinguere reviewer in rapporto da approvazione formale sulla PR |
| CORE [#173](https://github.com/2008hitch-afk/centrochange_core/issues/173) | **REQUISITO OWNER APPROVATO / IMPLEMENTATION_NOT_ATTESTED**; mandato [registrato](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6424378839) e inviato ad AGY dall'Owner | Non è già sviluppato o installato; non attivare in parallelo a GOAL #171 ancora senza gate |
| Tracker generale [#156](https://github.com/2008hitch-afk/centrochange_core/issues/156) | **GET 404 con identità GitHub disponibile** al checkpoint; URL esistente nelle istruzioni, contenuto non leggibile | **NON** dichiarare aggiornamento né crearne un duplicato alla cieca |

### Regola del passaggio

1. **Prima** completare la riconciliazione tecnica di #171, inclusa verifica browser con account Professional dell'avviso su Auto Locked e assenza pulsante `Riapri`; reviewer indipendente della SHA e rapporto finale, senza ripetere i PASS Owner.
2. Distinguere `READY_FOR_SCOPED_OWNER_ACCEPTANCE` da `OWNER_ACCEPTED`. **Solo l'Owner può approvare il perimetro #171**; la discussione sul miglioramento del blocco non è un'accettazione automatica.
3. Nessun merge #172 senza autorizzazione separata; documentare eventuale base/dependency della futura PR #173.
4. **Solo dopo il gate #171**, eseguire CORE #173 come singolo work package **backend + React + economia/report + ACL + audit**, senza espandere DEV. Per #173 occorre **nuovo gate DEV specifico**, non riutilizzare il gate #171.
5. La filiera Professionisti NON è `FINAL_ACCEPTED` finché #173 non supera UAT tecnico/Owner separati.

## 2. Matrice: 110 ID invariati, fonti e discrepanza risolta

Fonti e loro significato:
- [Dettaglio CSV](FUNCTIONAL-COVERAGE-DETAIL.csv): **110 righe**, ciascuna con codice, prova, stato tecnico, issue, gap e stato Owner. Il CSV è l'inventario degli ID, NON una percentuale di consegna o accettazione.
- [Matrice leggibile](FUNCTIONAL-COVERAGE-MATRIX.md): gerarchia per aree e cronologia di addendum; il **primo** addendum di fase attuale prevale sui riepiloghi storici che restano immutati.
- [Oracle AUDIT-05](AUDIT-05-PROFESSIONALS.md): casi, ruoli, gate e prove di #171, alcuni report sono fotografie tecniche antecedenti al candidato finale.

**Distribuzione CSV esatta su branch PR #172 / checkpoint documentale:** `12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED = 110`. Nel Markdown della PR prima del checkpoint era riportato **11/61/27/11**: conteggio testuale non coerente, qui rettificato senza cambiare gli stati tecnici dei 110 record. Su `main` precedente all'integrazione #172: **11/59/29/11**; non trattare le due revisioni come stesso stato o come aumento percentuale di funzionalità accettate.

**Revisione puntuale di questa fase:** 23 righe del CSV hanno ricevuto link logici a #171/#173, evidenze UAT, limiti e gate; **zero cambi ai valori di `Stato` e `Owner` rispetto alla HEAD #172**. Nessuna riga futura promossa, rimossa o ridefinita.

### Requisiti di primo livello da non perdere

| ID | Stato tecnico attuale | Evidenza/limite preciso |
|---|---|---|
| `CC-CAP-002`, `CC-EXT-004`, `CC-EXT-009` | PARTIAL / PASS / PARTIAL | Ricerca e scheda Professionisti, ruoli, modifica scoped nel clone, Owner verifica visiva; no aggiornamento di ruoli/DB DEV |
| `CC-CAP-005`, `033`, `039`, `CC-CAP-018` | PARTIAL | Sicurezza per i percorsi esercitati, note private e IDOR; non promuovere intera app |
| `CC-CAP-007`, `CC-CAP-034` | PARTIAL | Disponibilità multi-fascia e audit; UAT-05-35 mostra `Martedì: nessuna fascia -> 09:00–12:00`; test mutativi solo clone |
| `CC-CAP-014`, `CC-ACT-004` | PARTIAL | Chiusura **singola** e CC Settlement tecnico, scelta POS visiva UAT-05-32; NON è «Chiudi la mia giornata» |
| `CC-CAP-022`, `CC-ACT-005` | PARTIAL / NOT_TESTED | Stato Auto Locked e legacy `Riapri`; recupero autonomo **non implementato**, da fare in #173 |
| `CC-CAP-023`, `CC-CAP-024`, `CC-CAP-027` | PARTIAL | Job 21:00/07:00 testati su clone; UAT-05-36 messaggi storici italiani; **delivery + recupero tardivo** da provare in #173 |
| `CC-CAP-025`, `CC-ACT-006` | NOT_TESTED | Regola 48h / DST non dichiarata PASS sulla sola UAT; #173 riusa fatti storici senza creare debiti retroattivi |
| `CC-CAP-028` | PASS tecnico / Owner PENDING | Report per ruolo, UAT-05-37 2 sedute bloccate/Da definire; UAT-05-38 CSV 2 righe concordanti |
| `CC-EXT-005`, `CC-CAP-029` | PARTIAL | Export fotografato, senza prova Owner sui bytes raw, altri report/stampe/email; test di regressione separati |
| `CC-EXT-026` | PARTIAL | Italiano/date/24h nelle superfici corrette, ma issue globale #134 OPEN: non promuovere l'intera app |

## 3. Owner UAT finale #171 — esiti verificati, e residuo preciso

| ID UAT | Owner osserva | Esito delimitato |
|---|---|---|
| [UAT-05-35](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424029516) | Audit orario `Martedì: Nessuna fascia -> 09:00–12:00` | **PASS VISIVO** |
| [UAT-05-36](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424060422) | Notifiche: `100,00 €`, scadenze `15/10/2026`, `30/09/2026` e reminder in italiano | **PASS VISIVO**, non prova di consegna nuova notifica |
| [UAT-05-37](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424126085) | Periodo `12/10–14/10`: 2 sedute in `Bloccata` e `Da definire`, 0 svolte, 0 pagamento, importo dovuto nel riepilogo 0,00 € | **PASS VISIVO** |
| [UAT-05-38](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424152452) | LibreOffice CSV, 12 colonne e 2 righe `Bloccata/Da definire`, importo tariffa originaria informativo | **PASS VISIVO**, non il file grezzo |
| [UAT-05-39](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6424190750) | Drawer Direzione su 12/10: `Riapri` visibile, nota Auto Locked assente | **NOT APPLICABLE per Manager**: codice `views.tsx` mostra nota soltanto a `!administrative`; manca evidenza visiva CC Professional |
| Decisione Owner metodi POS [UAT-05-32](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6422956400) | POS/Contanti multipli leggibili | **ACCETTATO COME UX**; quantità reali cliente da concordare all'handoff, no cancellazioni |

**Residuo Owner minimo #171:** non rifare il walkthrough completo. Serve prova browser reale come Professional sulla stessa seduta 12/10 (avviso visibile, `Riapri` assente) e verifica del reviewer indipendente sul commit finale; poi chiedere una sola accettazione **circoscritta** a #171, senza confondere questo gate con #173 o con il merge.

## 4. Requisito CORE #173 — cosa è approvato e cosa manca

**Vincolo cliente/Owner:** nessun professionista deve chiamare Direzione/Segreteria ogni mattina per sbloccare sedute proprie dimenticate.

**Definito in [Issue #173](https://github.com/2008hitch-afk/centrochange_core/issues/173) e [mandato AGY](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6424378839)**; **NON IMPLEMENTATO / NON INSTALLATO al checkpoint**.

- UX «Chiudi la mia giornata»: scegliere oggi o una giornata arretrata; sole sedute proprie, esito Svolta sì/no, Pagata sì/no ove applicabile e metodo canonico esplicito; anteprima e **una sola conferma**.
- Ore 21:00: promemoria interno se rimangono pendenti; ore 07:00: evento di blocco storico e controllo dell'irrisolto, **mai ostacolo permanente** alla finalizzazione tardiva del Professional proprietario.
- Backend: **endpoint autorizzato specifico**, senza `reopen` generico e senza modifica di sedute già consolidate; idempotenza, conflitti, audit append-only, timestamp seduta vs finalizzazione conservati.
- Semantica contabile: prestazione ≠ pagamento operativo ≠ fattura/Payment Entry; Pending non dovuto automaticamente; non interpretare ora tardiva come data cancellazione 48h.
- Test reali clone: A 4 sedute e B negato 403, Centro B/inattivo/Guest negati, job 21/07 con DST, rollback/retry, Report/CSV prima/dopo e dispositivo mobile. No suite simulata come unica prova.
- **Gate attuale:** lavoro AGY avviato con prompt dall'Owner, ma avanzamento tecnico va verificato su GitHub; il mandato stesso impone **chiusura/accettazione scoped #171 prima di scrivere nuovo codice #173** e **nuova autorizzazione DEV dedicata** prima dell'installazione. **Nessun merge o produzione autorizzati.**

## 5. Fonti e ordine di lettura obbligatorio per ogni ripresa AGY/Codex

1. **Questo checkpoint**, seguito dai due file matrice CSV+MD del medesimo commit.
2. [Issue #171](https://github.com/2008hitch-afk/centrochange_core/issues/171), [PR #172](https://github.com/2008hitch-afk/centrochange_core/pull/172), suo **SHA/CI effettivo** e rapporti UAT-05-35..39; verificare decisione Owner separata dalla review.
3. [Oracle AUDIT-05](AUDIT-05-PROFESSIONALS.md): API, DB, ACL, test; interpretare i checkpoint di commit passati come storico, non come ultimo runtime.
4. [Issue #173](https://github.com/2008hitch-afk/centrochange_core/issues/173) e mandato esecutivo #6424378839; eseguire solo dopo gate #171, nell'ordine.
5. [Design System](../ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md) come orientamento grafico storico; **in caso di conflitto, l'architettura attuale approvata Premium React + Frappe/ERPNext v16 + Marley + centrochange_core prevale** su passaggi datati del documento che descrivono UI Tabler senza React. Anche [roadmap MVP storica](../MVP-GOAL-ROADMAP-v0.1.md) non sostituisce il tracker corrente degli audit.

### Consistenza e igiene anti-smarrimento (check finale obbligatorio)

Ad ogni fine ciclo annotare su Issue attiva e nel documento di fase: GOAL esatto; branch/HEAD/CI; patch API/frontend/backend; stato PR/reviewer formale vs report; clone tecnico vs DEV read-only vs Owner; pass/partial/block e residui; fingerprint DB/backup/restore/rollback e fixture; matrice 110 ID, conteggi calcolati dal CSV, acceptance espressa; seguente GOAL **solo se autorizzato**. Nessun check `PASS` se prova incompatibile col requisito. Non riportare segreti o dati reali in GitHub.
