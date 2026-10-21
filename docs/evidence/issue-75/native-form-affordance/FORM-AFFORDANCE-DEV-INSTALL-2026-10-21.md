# PR #146 — installazione DEV autorizzata del 21/10/2026

**Esito: `ROLLED_BACK`.** Un solo tentativo di installazione; nessun secondo deploy. Il DEV condiviso è tornato alla baseline e resta disponibile. La PR #146 rimane DRAFT.

## Identità e gate

- HEAD PR autorizzata `cc21fa3104732cedb4b6c0f73d24ec0af1e927a8`; worktree pulito prima dell'esecuzione.
- Sorgente candidato `1f88207c6a71c4bf0252b912fe83313337cab16f`; executor SHA-256 `6503e7ed4b49863150cf6e4a06b0d848569c95052102264ac60abf891ffea12c`; overlay SHA-256 `1dc3d7b91d8176e48df2ae613593f2bfa41911d59a20a92882b591ec8b2bb9a9`. Tutti corrispondenti.
- `DRY_RUN_PASS` iniziale: 9 servizi, 2 centri, immagine baseline `sha256:6ecc23d0fe6ddc25b294d265546889aedee6049849a2cf58358f0087cb6c611e`, fingerprint dati `82dc3825e195bbcd9300f0a6787c043b9f105db324752f06ea3aae23afec7ecd`.
- Gate privato #75 creato il `2026-10-21T08:58:49Z`, scadenza operativa `12:58:49Z`, recupero `13:58:49Z`. Nessun segreto del gate è pubblicato.

## Sequenza ed esito

1. Checkpoint delle configurazioni e sei tag immagini rollback: verificato.
2. Immagine candidata costruita: `sha256:58b5dde4938f3e15db559103e6a554d590af42e14b5a2fdc7cdafd73b6445a55`.
3. Backup nativo cifrato di database, file pubblici, file privati e configurazione: quattro parti presenti; l'executor ha verificato decifratura e SHA-256 di ciascuna. Plaintext temporaneo rimosso.
4. Sei servizi applicativi avviati con il candidato. Verifiche asset, proxy realtime, schema, centri, fingerprint dati e permessi superate fino al browser gate.
5. Gate browser `mvp_devfirst_readonly.cjs`: `CRITICAL_FAIL` per la sola voce `m:execution`, eccezione `TimeoutError` durante il login. Il runner si aspettava il completamento della navigazione dopo la credenziale della fixture.
6. Diagnosi read-only dopo rollback: l'utente demo Direzione esiste ed è abilitato; `check_password` della password nella fixture privata `demo-owner.json` restituisce **NO**. Il file fixture risale al 12/10/2026; la password di quell'account è stata successivamente reimpostata con autorizzazione Owner. Nessun valore di password è stato mostrato o registrato. Il test non ha dimostrato un difetto del candidato UI.
7. L'executor ha eseguito l'unico rollback. `rollback_failure: null`; immagini dei nove servizi, schema, dati, permessi e hook verificati dal percorso di recupero. Il `--dry-run` ripetuto sulla baseline restituisce ancora `DRY_RUN_PASS` con la stessa impronta dati. Login HTTP locale `/login`: 200.

Report privato integrale e backup: `~/.local/state/centrochange-single/issue75-form-affordance-install-runs/20261021T085903Z-1057381/`. Non pubblicare dump, chiavi, fixture o diagnostica grezza.

## Stato e limite

Il DEV **non serve** la correzione #146: backend e frontend sono tornati all'immagine baseline `sha256:6ecc23d0fe6ddc25b294d265546889aedee6049849a2cf58358f0087cb6c611e`; 9/9 servizi attivi. Le verifiche visuali post-installazione di Pazienti, Professionisti, Finance, Agenda e localizzazione **non sono state completate**. Le prove CSS in anteprima e nel clone restano evidenza preparatoria, non live.

Prima di un eventuale nuovo gate occorre rendere il browser gate indipendente dalla password Direzione non più valida nella fixture, senza esporre o reimpostare credenziali e senza abbassare i controlli di sicurezza. Questo tentativo ha consumato l'autorizzazione al singolo aggiornamento; nessun retry automatico è consentito.
