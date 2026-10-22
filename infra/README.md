# Centro Change DEV runtime

> **#148 single-stack:** la recipe è `Dockerfile.single-stack-full` con `compose.single-stack-full.yaml` e `verify_full_single_stack.py`. I tentativi, il rollback e la successiva installazione DEV delimitata sono registrati nei report DECISION-064–066 e nel report UAT del 22/10/2026; verificare immagine/HEAD effettive prima di qualsiasi nuova operazione. Il [piano storico di esecuzione](../docs/ui/premium-react/SINGLE-STACK-COMPLETE-REBUILD-EXECUTION-PLAN.md) non autorizza un nuovo deploy o migrate. Il vecchio `Dockerfile`/`compose.yaml` sotto è il bootstrap GOAL-01 storico e non va usato per installare il candidato React. Il precedente overlay premium è stato revocato.

Questo Compose project è il bootstrap DEV di WP-00 / issue #21. È isolato dagli altri progetti. Vedi `docs/RUNTIME-BASELINE.md` per naming e pin storici e `docs/evidence/WP-00-2026-10-04.md` per lo stato della nuova validazione.

Il build recupera Builder e Marley/Healthcare ai tag dichiarati nel Dockerfile e verifica i commit esatti. Gli asset includono Frappe, ERPNext, Builder, Healthcare e Centro Change. `socketio_port=9000` viene impostato prima del build Marley; gli asset compilati sono copiati nella directory `assets` che l'entrypoint ufficiale espone nel volume sites.

Su un site nuovo il configuratore installa ERPNext/Builder, imposta `cc_synthetic_dev=1`, esegue il wizard nativo con la company `Centro Change SYNTHETIC DEV` (Italy/EUR, anno fiscale 2026), installa Healthcare e Centro Change, migra e abilita lo scheduler. Il helper è importabile dall'image prima dell'installazione dell'app sul site. Non è whitelisted.

Il setup verifica flag DEV, identità Administrator, company, valuta, paese e presenza del piano contabile. Non promuove automaticamente un site preesistente a DEV sintetico. Se un volume precedente non ha il flag, il configuratore si arresta: usare un ambiente fresco e isolato dopo aver verificato che gli eventuali volumi da eliminare contengano esclusivamente dati DEV sintetici.

Non usare questi input per produzione.

## Acceptance ripetibile

Con lo stack già avviato, eseguire dall'host con accesso Docker:

```sh
python3 infra/runtime_acceptance.py --env-file /percorso/esterno/runtime.env --snapshot /tmp/cc-baseline-a.json
```

Il harness verifica ping, login Administrator, Desk, asset HTTP Frappe/ERPNext/Healthcare/Builder, upgrade WebSocket, scheduler abilitato, due worker e job completati su short/long. Verifica anche il rifiuto RPC del helper e il rifiuto di setup sotto Guest/senza flag DEV (solo modifiche in memoria della sessione bench). Esegue `centrochange_core.dev_bootstrap.smoke`: Patient, Practitioner, Appointment e Appointment Type sintetici sono inseriti tramite il nativo e annullati con rollback; il conteggio dei tre master operativi deve tornare a zero. Usare solo il site fresco sintetico: il harness rifiuta fixture preesistenti sui tre DocType.

Per destroy/recreate, usare `docker compose -f infra/compose.yaml --env-file … down --volumes` **solo dopo aver verificato che i volumi `centrochange-dev-*` contengano esclusivamente i dati DEV sintetici di questo test**, riavviare la stessa recipe e ripetere il harness su `/tmp/cc-baseline-b.json`. `cmp /tmp/cc-baseline-a.json /tmp/cc-baseline-b.json` deve passare. Lo snapshot normalizza app installate, setup, country/currency company, inventario DocType/module e conteggi sintetici; non afferma uguaglianza byte-per-byte di DB o image.

In una sessione precedente all'aggiunta del gruppo Docker, `sg docker -c '…'` carica il gruppo aggiornato senza sudo. Credenziali, cookie, configurazioni site e log grezzi restano fuori Git. Risultati e limiti della validazione corrente sono nell'evidenza WP-00 collegata sopra.
