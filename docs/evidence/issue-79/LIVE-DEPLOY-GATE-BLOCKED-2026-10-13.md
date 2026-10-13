# #79 — deploy CSS live: BLOCKED al preflight

Mandato Owner: [commento #6153014994](https://github.com/2008hitch-afk/centrochange_core/issues/79#issuecomment-6153014994). Il mandato impone STOP se mancano privilegi, verifica immagine/sorgenti o rollback riproducibile. **Nessun deploy è stato tentato.**

## Stato verificato

- PR #129 DRAFT/OPEN, HEAD `1b2486d00754ba68fa4ee3c57a39060dc8cc781c`, base PR #127. Worktree `issue-79/unified-desk-autocomplete` pulito prima di questo report. Delta applicativo del commit autorizzato: soltanto due regole in `cc_unified_desk.css`; #128 esclusa.
- La route HTTP DEV su `127.0.0.1:8082/login` risponde 200. Questo non prova identità immagine né salute dell'intero Compose.
- Identità ambiente corrente: host `srv2033673`, uid `empv26`, gruppi `empv26,sudo,users`. Socket `/var/run/docker.sock` di `root:docker` (`0660`); l'utente non appartiene al gruppo `docker`.
- `docker ps --filter label=com.docker.compose.project=centrochange-dev` termina con `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`.
- SSH BatchMode verso l'host indicato nella documentazione Owner termina con `Permission denied (publickey,password)`. Nessuna sessione remota aperta.

**Impedimento unico:** manca un canale operativo autorizzato per leggere e controllare Docker sull'host che serve il DEV. Non si possono verificare immagine e servizi, fissare un checkpoint/rollback attendibile o ricreare i soli servizi necessari. Proseguire violerebbe il Gate 1 esplicito dell'Owner.

## Nessuna mutazione runtime

Nessuna build, `docker compose up`, restart, patch container, clear-cache, migrazione, seed, modifica DB, merge o lavoro #128. Nessun rollback eseguito perché nessuna modifica al DEV è stata effettuata. Il test Chromium `live` non è stato ripetuto: avrebbe soltanto confermato il difetto già noto sul CSS precedente e non avrebbe risolto il blocco di accesso.

## Minima condizione per riprendere

Fornire a questa identità accesso operativo autorizzato al Docker del solo host DEV (o un executor equivalente con permessi e identità verificabili) e accesso SSH valido se il Docker target è remoto. Poi ripartire dal Gate 1: immagine/source diff, salute, checkpoint e rollback **prima** del deploy del solo CSS. PR #129 resta DRAFT. Nessun `LIVE_TECHNICAL_PASS` o Owner PASS è dichiarato.
