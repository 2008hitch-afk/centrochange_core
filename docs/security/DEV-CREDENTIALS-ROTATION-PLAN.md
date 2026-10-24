# Piano di Rotazione Credenziali DEV Compromesse

> [!CAUTION]
> **STATO PIANO: IN ATTESA DI AUTORIZZAZIONE ESPLICITA OWNER.**
> In osservanza delle policy di sicurezza e della SOP v1.1, questo piano è documentato a scopo di audit e remediation, ma **NON DEVE ESSERE ESEGUITO** prima della formale autorizzazione dell'Owner.
> Nessun deploy o rotazione live è in corso durante la sessione corrente.

---

## 1. Descrizione dell'Evento e Perimetro

### 1.1 Descrizione
Nel commit `96bffaf` del branch `issue-171/professionals-audit` (PR #172), nell'implementazione preliminare dello script di test volumetrico `infra/clone_volume_test.py`, è stata inclusa la stringa della password del database MariaDB di sviluppo (`_4f614b4543aa5230`).

### 1.2 Perimetro di Rischio e Valutazione d'Impatto
- **Ambiente coinvolto:** Esclusivamente ambiente di sviluppo locale/DEV Docker (`127.0.0.1:8082`), con flag esplicito `cc_synthetic_dev=1`.
- **Dati reali / Produzione:** **NESSUN IMPATTO**. Il repository e l'ambiente DEV contengono solo fixture sintetiche. Nessun dato reale, clinico, anagrafico o di produzione è presente né è mai stato esposto.
- **Rimedio immediato nel codice:** Tutte le credenziali hardcoded sono state rimosse dal repository, dai test e dagli script di supporto. `infra/clone_volume_test.py` acquisisce le credenziali DEV dinamicamente dal container a runtime e impiega password effimere (`secrets.token_hex(16)`) per i container isolati di test.
- **Azione richiesta:** Rotazione della password dell'utente DB `_4f614b4543aa5230` sull'ambiente DEV attivo, previa approvazione Owner.

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

## 4. Procedura di Rollback

Nel caso in cui si verifichino errori imprevisti durante il riavvio o la connessione applicativa:
1. Ripristinare l'utente MariaDB con la password precedente temporanea:
   ```bash
   docker exec -i centrochange-dev-db-1 mariadb -u root -p"$MYSQL_ROOT_PASSWORD" -e "
     ALTER USER '_4f614b4543aa5230'@'%' IDENTIFIED BY '<PREVIOUS_PASSWORD>';
     FLUSH PRIVILEGES;
   "
   ```
2. Ripristinare `db_password` in `site_config.json`.
3. Riavviare i servizi `backend`, `queue-short`, `queue-long`, `scheduler`.
4. Documentare il blocco e consultare l'Owner.
