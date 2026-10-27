# Piano di Rotazione Credenziali DEV Compromesse

> [!NOTE]
> **STATO PIANO: ESEGUITO CON SUCCESSO SU FORMALE AUTORIZZAZIONE OWNER (25/10/2026).**
> In seguito all'autorizzazione esplicita Owner (commento GitHub [#6390491080](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6390491080)), la procedura di rotazione è stata eseguita con esito **PASS_ROTATION_SUCCESS**.
> - Backup cifrato GPG e prova di restore isolata superata (`PASS_RESTORE_VERIFIED`).
> - Vecchia credenziale esposta storicamente revocata e definitivamente respinta da MariaDB con `ERROR 1045 (28000): Access denied`.
> - Nuova credenziale forte (128-bit di entropia) allineata su MariaDB e `site_config.json`.
> - Servizi applicativi riavviati e verificati con `bench doctor` (2 worker online, 0 job bloccati).
> - Zero esposizione di credenziali in log, CLI o Git.

---

## 1. Descrizione dell'Evento e Perimetro

### 1.1 Descrizione
Nel commit `96bffaf` del branch `issue-171/professionals-audit` (PR #172), nell'implementazione preliminare dello script di test volumetrico `infra/clone_volume_test.py`, è stata inclusa la stringa della password del database MariaDB di sviluppo (`_4f614b4543aa5230`).

### 1.2 Perimetro di Rischio e Valutazione d'Impatto
- **Ambiente coinvolto:** Esclusivamente ambiente di sviluppo locale/DEV Docker (`127.0.0.1:8082`), con flag esplicito `cc_synthetic_dev=1`.
- **Dati reali / Produzione:** **NESSUN IMPATTO**. Il repository e l'ambiente DEV contengono solo fixture sintetiche. Nessun dato reale, clinico, anagrafico o di produzione è presente né è mai stato esposto.
- **Rimedio nel codice sorgente e harness:** Tutte le credenziali hardcoded sono state rimosse dal repository e dai test. Lo script `infra/clone_volume_test.py` acquisisce le credenziali DEV dinamicamente a runtime, usa file di opzioni effimeri a permessi 0600 per non esporre password nella process list (`ps aux`) o argomenti CLI, e impiega token casuali ad alta entropia (`secrets.token_hex(16)`) per MariaDB clonata.
- **Tracciabilità Git History:** Si prende atto che il commit storico `96bffaf` conserva traccia della stringa precedente nel reflog/history. La rotazione sul DB DEV renderà la stringa storicizzata totalmente invalida e inerte.
- **Azione richiesta:** Rotazione della password dell'utente DB `_4f614b4543aa5230` sull'ambiente DEV attivo, **esclusivamente previa autorizzazione formale dell'Owner**.

---

## 2. Risorse Oggetto della Rotazione

| Risorsa | Posizione / Riferimento | Note |
|---|---|---|
| Utente MariaDB | `_4f614b4543aa5230`@`%` nel container `centrochange-dev-db-1` | Utente proprietario del DB applicativo DEV |
| Database | `_4f614b4543aa5230` | Database applicativo Frappe / ERPNext |
| Config Frappe Site | `/home/frappe/frappe-bench/sites/centrochange.local/site_config.json` | Chiave `db_password` |
| File Env Compose | File `.env` privato usato da Docker Compose DEV | Variabile `DB_PASSWORD` |
| Servizi da riavviare | `backend`, `queue-short`, `queue-long`, `scheduler` | Processi applicativi collegati al DB |

---

## 3. Runbook Operativo di Rotazione (Solo su Autorizzazione Owner)

Qualora l'Owner autorizzi formalmente l'esecuzione, il runtime engineer eseguirà la seguente procedura passo-passo in una finestra di manutenzione concordata:

### Fase 1: Preflight e Generazione Segreto
1. Verificare che non vi siano transazioni critiche o job asincroni pendenti:
   ```bash
   docker exec centrochange-dev-backend-1 bench --site centrochange.local doctor
   ```
2. Generare un nuovo segreto ad alta entropia (32 caratteri esadecimali):
   ```bash
   NEW_DB_PASS=$(openssl rand -hex 16)
   ```

### Fase 2: Aggiornamento Utente in MariaDB
1. Eseguire l'alterazione della password direttamente sul server MariaDB:
   ```bash
   docker exec -i centrochange-dev-db-1 mariadb -u root -p"$MYSQL_ROOT_PASSWORD" -e "
     ALTER USER '_4f614b4543aa5230'@'%' IDENTIFIED BY '${NEW_DB_PASS}';
     FLUSH PRIVILEGES;
   "
   ```

### Fase 3: Aggiornamento Configurazione Applicativa
1. Aggiornare `site_config.json` sul site `centrochange.local`:
   ```bash
   docker exec -i centrochange-dev-backend-1 python3 -c "
   import json
   path = 'sites/centrochange.local/site_config.json'
   with open(path) as f:
       cfg = json.load(f)
   cfg['db_password'] = '${NEW_DB_PASS}'
   with open(path, 'w') as f:
       json.dump(cfg, f, indent=1)
   "
   ```
2. Aggiornare il file env privato di Compose per mantenere coerenza al successivo `docker compose up`.

### Fase 4: Riavvio dei Servizi Applicativi
1. Riavviare i container applicativi per ricaricare la connessione al database:
   ```bash
   docker compose -p centrochange-dev restart backend queue-short queue-long scheduler
   ```

### Fase 5: Verifica e Collaudo Post-Rotazione
1. **Connessione con la nuova credenziale (atteso: SUCCESS):**
   ```bash
   docker exec -i centrochange-dev-db-1 mariadb -u _4f614b4543aa5230 -p"${NEW_DB_PASS}" _4f614b4543aa5230 -e "SELECT 1;"
   ```
2. **Reiezione della vecchia credenziale esposta (atteso: Access Denied / ERROR 1045):**
   ```bash
   docker exec -i centrochange-dev-db-1 mariadb -u _4f614b4543aa5230 -p"<PREVIOUS_EXPOSED_PASSWORD>" _4f614b4543aa5230 -e "SELECT 1;"
   # Codice di uscita atteso: != 0 (Access Denied)
   ```
3. **Health check Frappe Bench:**
   ```bash
   docker exec centrochange-dev-backend-1 bench --site centrochange.local doctor
   ```
4. **Smoke test endpoint HTTP:**
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8082/api/method/frappe.auth.get_logged_user
   ```

---

## 4. Procedura di Ripristino e Rollback Sicuro (Roll-Forward Only)

> [!CAUTION]
> **REGOLA FONDAMENTALE DI SICUREZZA: LA VECCHIA CREDENZIALE ESPOSTA NON DEVE MAI ESSERE RIATTIVATA.**
> In caso di anomalie o fallimento della rotazione su DEV, è categoricamente vietato tentare il ripristino della password precedentemente compromessa. Il rollback si attua esclusivamente mediante una procedura di **Roll-Forward** con un segreto di emergenza alternativo fresco oppure mediante restore da backup a freddo pre-rotazione a cui viene immediatamente assegnata una credenziale nuova non esposta.

### Procedura di Roll-Forward di Emergenza
Qualora i servizi applicativi non si riconnettano correttamente con la prima credenziale ruotata (`NEW_DB_PASS`):
1. **Generazione di una nuova credenziale alternativa (Roll-Forward Rescue):**
   ```bash
   RESCUE_DB_PASS=$(openssl rand -hex 16)
   ```
2. **Aggiornamento immediato in MariaDB con il segreto di rescue:**
   ```bash
   docker exec -i centrochange-dev-db-1 mariadb -u root -p"$MYSQL_ROOT_PASSWORD" -e "
     ALTER USER '_4f614b4543aa5230'@'%' IDENTIFIED BY '${RESCUE_DB_PASS}';
     FLUSH PRIVILEGES;
   "
   ```
3. **Allineamento configurazione Frappe e Compose:**
   - Aggiornare `db_password` in `sites/centrochange.local/site_config.json` con `${RESCUE_DB_PASS}`.
   - Aggiornare `DB_PASSWORD` nel file `.env` privato di Compose con `${RESCUE_DB_PASS}`.
4. **Riavvio ordinato dei container applicativi:**
   ```bash
   docker compose -p centrochange-dev restart backend queue-short queue-long scheduler
   ```
5. **Verifica connessione e isolamento:**
   - Verificare che `SELECT 1` risponda con `${RESCUE_DB_PASS}`.
   - Verificare che il tentativo di connessione con la vecchia credenziale esposta venga rifiutato con `Access denied`.
6. **In caso di blocco persistente:**
   - Arrestare i servizi (`docker compose -p centrochange-dev stop backend queue-short queue-long scheduler`).
   - Mantenere il database nello stato congelato senza mai esporre segreti nei log.
   - Segnalare l'anomalia all'Owner con log privi di credenziali.
