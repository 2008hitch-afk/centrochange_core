# EMPV — Ciclo di feedback rapido per web app (v1.1)

**Ambito:** sviluppo in worktree e ambiente isolati. Questo è un adattatore di esecuzione per la SOP Goal-Driven esistente: non è una nuova Factory, non è un orchestratore Codex, non fa deploy e non concede autorizzazioni.

## Da Goal a risultato in due velocità

**Durante la vertical slice:** requisiti e User Journey approvati → piccola modifica UI/API → server di sviluppo e preview live → test mirati/Playwright → diagnosi (APP, HARNESS, AUTH, INFRA o DESIGN) → correzione e ripetizione autonoma. Non chiedere all'Owner di trovare difetti ordinari.

**Quando il candidato è stabile:** suite integrata backend reale su clone consentito, CI, design review indipendente, prove per ogni interfaccia modificata e richiesta di gate DEV/STAGING separato se necessario. L'UAT finale dell'Owner riguarda il risultato, non i micro-passaggi. `PASS_LOCAL`, mock, `PASS_LIVE` e `OWNER_ACCEPTED` restano diversi.

## Il runner riutilizzabile

Il bootstrap v1.1 copia nei nuovi progetti `scripts/dev_feedback.py`, `factory/dev-feedback.example.json` e un `.gitignore` che esclude i report locali. Richiede solo Python standard: **non** installa npm, browser, Codex, Docker o nuove dipendenze.

Su una macchina di sviluppo del progetto, copiare l'esempio e adattarlo ai comandi del framework:

```sh
cp factory/dev-feedback.example.json factory/dev-feedback.json
python3 scripts/dev_feedback.py doctor
```

Il file JSON definisce `cwd`, `preview.command`, `preview.ready_url` e `suites`. Ogni comando è un array di argomenti, non una stringa shell. L'URL di readiness deve essere su `http://127.0.0.1:PORT` o `http://localhost:PORT`. Il server va vincolato a loopback; usare un tunnel SSH autenticato se è remoto.

```sh
# Terminale 1 — server frontend del progetto; Ctrl+C per arrestarlo
python3 scripts/dev_feedback.py preview

# Terminale 2 — controllo e suite selezionate, ripetibili dopo ogni correzione
python3 scripts/dev_feedback.py check
python3 scripts/dev_feedback.py test --suite typecheck
python3 scripts/dev_feedback.py test --suite ui
```

Il comando `test` tenta di terminare l'intero gruppo di processi su POSIX quando va in timeout; su Windows l'arresto dei processi figli dipende dal comando. Il comando `test` propaga il vero exit code e crea un rapporto in `.factory-runtime/last-NOME.json` con SHA git, ora e stato `PASS_LOCAL`/`FAIL_LOCAL`. Questo **non prova** che il browser abbia attraversato il flusso atteso: Codex deve aprire la pagina, controllare gli esiti e produrre evidenze affidabili. Il file `factory/dev-feedback.json` e i rapporti in `.factory-runtime/` sono esclusi dal Git dei progetti generati. Non committare log, screenshot o dati sensibili senza sanitizzazione.

## Progetto su un server, browser sul PC

Se la preview gira su un server di sviluppo Linux vincolato a `127.0.0.1:5182`, sul PC Windows:

```powershell
ssh -N -L 5182:127.0.0.1:5182 utente@server-di-sviluppo
```

Aprire nel browser Windows la URL locale corrispondente. Non esporre Vite o la UI di debug su Internet. Questo è un esempio per ambiente autorizzato, non una configurazione già applicata al server.

### Adattamento a Centro Change (solo esempio tecnico)

In `frontend/premium` esistono già React/Vite e Playwright. In **worktree isolato**, configurare `cwd=frontend/premium`, comando preview `["npm","run","dev"]` e URL `http://127.0.0.1:5182/assets/centrochange_core/premium/`. Usare le suite Playwright esistenti. Attenzione: una suite sintetica può tentare di usare la **stessa porta 5182** della preview. Va destinata a una porta di test distinta, oppure fermare la preview prima dei test; non riutilizzare per errore un server con fixture/modalità diverse. Non modificare lo STAGING per questo esempio.

Per Laravel, Frappe o un'altra web app, sostituire esclusivamente i comandi previsti dal progetto. Nessun obbligo di adottare Vite, React o un nuovo frontend.

## Gate per Draft e PR pronta

La PR #3 introduce un controllo UI a due livelli. Per una **Draft PR**, `verify_ui_diff.py --stage draft` richiede almeno un Goal con `ui_impact=YES` in stato `ACTIVE` (o successivo), consentendo le correzioni prima dell'UAT finale. Al passaggio a **Ready for Review**, `--stage ready` richiede un Goal `READY_FOR_REVIEW` o `VERIFIED`. Il workflow generato riesegue il controllo anche sull'evento `ready_for_review`.

Questo controllo è **euristico**: non dimostra che ogni file modificato appartenga al Goal dichiarato né autentica un vero giudizio UX. La CI dovrà essere un required check attendibile e la review indipendente deve essere verificata prima di merge; le regole GitHub vanno attivate separatamente.

## Quando la Factory sarà davvero OPERATIONAL

Gli unit test sintetici del runner coprono preview localhost, readiness, fallimento/ripetizione di una suite e arresto del processo. Non dimostrano l'esecuzione di un agente AI su una web app cliente. Serve un **pilot reale isolato** con Codex o altro agente autorizzato: Goal e criteri, browser reale, difetto riprodotto e corretto, test mirati, CI sull'esatta SHA, reviewer indipendente ed evidenze. Solo con gate di integrazione/release testati e approvazione Founder potremo usare lo stato `OPERATIONAL`. Fino ad allora: `CANDIDATE_UNDER_VALIDATION`.
