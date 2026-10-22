# AUDIT-02 — Navigazione Premium React (#161)

**Stato:** `PARTIAL / OWNER_DEV_GATE`. Baseline `main` `335de5709e1c7b477be0b677f69913ecc2f6a9e6`; candidato nel branch `issue-161/premium-navigation`. La PR va revisionata, poi distribuita soltanto con gate Owner. Nessuna accettazione Owner o prova Frappe live del candidato è dichiarata.

## Baseline verificata

- #149, #150, #159 e #160 sono integrate in `main`; il worktree AUDIT-02 è isolato. Le modifiche della PR #160 sono nella baseline e non sono state riscritte.
- Unico Compose DEV osservato in sola lettura: sei servizi applicativi, MariaDB e due Redis attivi. I servizi applicativi usano `sha256:569909d92601328a4f2f9cdef356fff547d84b28bc986321ff4aea30d9bca063`, label sorgente `01abc5cb72b092b8c1738f6e097814d50292f114`, precedente a `main`. Il merge Git non ha aggiornato il runtime. Nessun container, Site o DB è stato modificato in AUDIT-02.
- `CC-EXT-002` è la capability shell; `CC-CAP-005/033/038/039` coprono segregazione e autorizzazione; `CC-EXT-027` copre desktop/mobile. Le decisioni 060–066 e `AGENTS.md` restano applicabili. Login Frappe #158 non è stato riaperto.

## Azioni, autorità e prove

`M` Manager, `S` Segreteria, `P` Professionista, `F` Finanza, `A` Contabile; i ruoli effettivi dipendono dalla sessione Frappe. `PASS_OFFLINE` indica test Python sintetico o browser con API intercettate; **non** equivale a PASS sul DEV.

| Azione / requisito | React e API | Fonte autorevole / ruoli | Prova candidata | Stato |
|---|---|---|---|---|
| Shell, logo, sidebar, header, breadcrumb, footer, Agenda predefinita (`CC-EXT-002/027`) | `main.tsx`, `style.css`; `workspace.bootstrap`, `reporting.bootstrap` | Sessione `User`, `Role`, `Branch`, `CC Center Membership`; sezioni da bootstrap autorizzato | Playwright desktop/mobile: shell, footer, menu, landing | PASS_OFFLINE; live `NOT_TESTED` |
| Voci per ruolo, area privilegiata nascosta (`CC-EXT-002/033`) | `main.tsx`, hash `#Agenda`…`#Notifiche`; API di ogni vista resta server-side | `Role`, DocPerm, Membership; M/S/P operativi, M/F/S/A secondo finanza, Guest negato da Frappe | Playwright ruolo operativo e solo Finanza; hash privilegiato ricondotto a route lecita | PASS_OFFLINE; sette ruoli + Guest live `NOT_TESTED` |
| URL diretto, hash malformato, F5, back/forward (`CC-EXT-002`) | `fromHash`, `hashchange`, canonicalizzazione con `replaceState` | Route React; bootstrap Frappe arbitro delle viste; API singola arbitra i dati | Playwright desktop/mobile: URL illecito e `%ZZ`, F5 e back | PASS_OFFLINE; accesso diretto Frappe live `NOT_TESTED` |
| Centro A/B e cancellazione stato precedente (`CC-CAP-005/039`) | `main.tsx` reset boot/query/drawer; `workspace.bootstrap`, `workspace.patient_search` | `Branch.cc_operational`, Membership, `CC Patient Assignment.active`, `Patient`; M/S/P nei centri consentiti | Python: Manager A/B, P limitato, centro non operativo, zero assegnazioni; Playwright risposta tardiva A scartata in B | PASS_OFFLINE; segregazione reale DB/API `NOT_TESTED` |
| Ricerca rapida e selezione paziente (`CC-EXT-002/005`) | `navigation_search.tsx` chiama `workspace.patient_search`; `views.tsx` apre la scheda Pazienti | `Patient.name` come ID canonico, `patient_name`, assegnazione attiva per centro; ruoli operativi, F/A senza bootstrap operativa: ricerca disabilitata | Playwright: suggerimento, selezione, query con centro, vuoto/errore, troncamento, mobile; Python scope server sintetico | PASS_OFFLINE; 403 e record live `NOT_TESTED` |
| Menu mobile, overlay, tastiera, focus, overflow (`CC-EXT-027`) | `main.tsx`, `navigation_search.tsx`, `style.css` | DOM/ARIA, nessun dato | Playwright 390×844: Escape, Tab, focus, `inert`, scrollWidth; screenshot ispezionati | PASS_OFFLINE; test su asset DEV `NOT_TESTED` |
| Logout e sessione condivisa (`CC-EXT-001`) | Menu utente e sidebar chiamano `POST /api/method/logout` tramite `api.ts` con CSRF; login resta nativo Frappe | `User`, sessione/cookie/CSRF Frappe; tutti gli autenticati | Playwright sintetico logout/CSRF; precedente #158: 10/10 live su vecchia immagine e Owner accesso/F5/Esci limitato | PASS_OFFLINE per candidato; live candidato `NOT_TESTED` |
| Carico, errore, area non disponibile (`CC-EXT-002`) | Skeleton/alert in `main.tsx`; ricerca con stato vuoto/errore | Esiti `workspace.bootstrap` e `reporting.bootstrap`; nessun bypass di 403 | Browser sintetico per shell e ricerca; nessun errore server simulato come PASS reale | PARTIAL; live `NOT_TESTED` |

## Difetti confermati e correzioni

1. **P0: pazienti di altri centri nel bootstrap Manager e nella ricerca.** `workspace.bootstrap` prendeva fino a 500 Patient senza filtro centro; `patient_search` ometteva il filtro per Manager. Ora entrambi limitano i nomi Patient tramite assegnazioni attive nel centro selezionato, prima della paginazione. La ricerca rifiuta centri non operativi e mantiene la verifica dei permessi DocType. Nessuna regola di assegnazione è stata cambiata.
2. **P1: ricerca globale non funzionante.** Il campo precedente filtrava soltanto la lista Pazienti dopo Enter. Ora suggerisce via API scoped, usa etichette demo soltanto per presentazione, limita a 50 righe, segnala troncamento/errori/vuoto, apre la scheda esistente e scarta risposte tardive al cambio centro. ID reali restano nelle API.
3. **P1: URL/hash illeciti, menu e focus mobile.** Hash malformato non causa più errore di render; URL non consentito converge sulla vista lecita; menu e ricerca mobile gestiscono focus, Escape e `inert`. Footer e menu utente completano la shell. Il logout resta il metodo Frappe esistente.

## Verifiche e limiti

| Controllo | Esito |
|---|---|
| Python offline sintetico, incluso scope negativo | **51/51 PASS** |
| React typecheck e build Vite | **PASS** |
| Manifest completo `verify_full_single_stack.py --source` dopo rigenerazione asset | **PASS** |
| Playwright sintetico desktop/mobile (suite generale) | **100 PASS, 8 SKIP**: casi vincolati al solo device previsto; nessun FAIL |
| Playwright scoped API desktop/mobile | **30/30 PASS** con risposte sintetiche |
| Browser live su immagine candidata, sette ruoli + Guest, centri A/B, 403 API, accessi diretti, sessione | **NOT_TESTED**: DEV contiene immagine precedente |
| Review/merge, installazione DEV e walkthrough Owner | **PENDING** |

Screenshot sanitizzati della build locale (solo fixture sintetiche): [ricerca desktop](../evidence/issue-161/audit-02-search-desktop.png) a 1440×900, [ricerca mobile](../evidence/issue-161/audit-02-search-mobile.png) e [menu mobile](../evidence/issue-161/audit-02-mobile-menu.png) a viewport 390×844. Sono stati ispezionati: nessun clipping orizzontale della shell; il menu chiuso non riceve Tab e quello aperto mostra il logo e il pulsante di chiusura sopra la testata. Non contengono sessioni, password o dati reali. Le suite Playwright intercettano le API: verificano l'interazione UI, non il comportamento del Site reale. Il test Python usa una finta API Frappe; la verifica server reale è il gate seguente. Timeout reale, lockout e reset email rimangono gap separati di #158.

## Unico gate DEV proposto all'Owner

Dopo review della PR, autorizzare **una** installazione controllata nell'unico `centrochange-dev` del candidato completo derivato dallo SHA approvato. Prima dello switch: verificare commit/manifest/immagine, configurazione privata tramite identità legittima, un solo Site e DB, RAM/disco/cgroup/OOM, dati esclusivamente sintetici; creare checkpoint cifrato integrale a sei componenti e dimostrare restore reale su risorse temporanee isolate con confronto Site/DB. Promuovere solo i sei servizi applicativi nel Compose canonico, preservando MariaDB, Redis, Site, DB, volumi, rete e porta; nessun migrate, reset o cambio permessi. Confrontare asset HTTP con build. Fermarsi al primo problema materiale e usare soltanto rollback dimostrato sicuro; rispettare il limite di 120 minuti di blocco scritture e conservare backup/immagine precedente. Non attivare `cc_premium_primary=1`.

Sul DEV allineato: provare Guest + sette ruoli sintetici, A/B, 403 reali e IDOR su ricerca/bootstrap, hash diretti, F5/back, sessione/logout, desktop 1440×900 e mobile 390×844, focus e screenshot. Solo dopo PASS reale, merge autorizzato, prova e accettazione Owner si può marcare #161 `DONE` e passare all'Agenda. Nessun gate di AUDIT-01 viene riaperto da questa proposta.

## Checklist breve Owner dopo il gate

1. Aprire `/premium` tramite l'accesso privato già autorizzato; accedere con account UAT sintetico dal canale sicuro.
2. Verificare ingresso, voci del proprio ruolo, navigazione Pazienti/Professionisti, URL diretto, F5 e back.
3. Se autorizzato per A/B, cambiare centro e cercare un paziente del centro precedente: non deve apparire. Aprire una scheda dal suggerimento.
4. Su mobile: aprire/chiudere menu e ricerca, usare Tab/Escape, verificare l'assenza di overflow; uscire e verificare il ritorno al login Frappe.
5. Registrare l'esito su #161 senza credenziali o dati sensibili.
