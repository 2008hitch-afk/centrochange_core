# Centro Change DEV runtime

Questo Compose project è il bootstrap DEV di WP-00 / issue #21. È isolato dagli altri progetti. Vedi `docs/RUNTIME-BASELINE.md` per naming e pin storici e `docs/evidence/WP-00-2026-10-04.md` per lo stato della nuova validazione.

Il build recupera Builder e Marley/Healthcare ai tag dichiarati nel Dockerfile e verifica i commit esatti. Gli asset includono Frappe, ERPNext, Builder, Healthcare e Centro Change.

Su un site nuovo il configuratore installa ERPNext/Builder, imposta `cc_synthetic_dev=1`, esegue il wizard nativo con la company `Centro Change SYNTHETIC DEV` (Italy/EUR, anno fiscale 2026), installa Healthcare e Centro Change, migra e abilita lo scheduler. Il helper è importabile dall'image prima dell'installazione dell'app sul site. Non è whitelisted.

Il setup verifica flag DEV, identità Administrator, company, valuta, paese e presenza del piano contabile. Non promuove automaticamente un site preesistente a DEV sintetico. Se un volume precedente non ha il flag, il configuratore si arresta: usare un ambiente fresco e isolato dopo aver verificato che gli eventuali volumi da eliminare contengano esclusivamente dati DEV sintetici.

Non usare questi input per produzione. La nuova recipe è in attesa di validazione runtime: non costituisce ancora evidenza di WP-00 PASS.
