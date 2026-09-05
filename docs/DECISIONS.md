# Technical Decision Log — Centro Change

Questo file registra **decisioni tecniche proposte o confermate** nel repository tecnico. Non sostituisce la validazione cliente dei requisiti funzionali.

## TD-001 — Piattaforma

**Stato:** PROPOSTA / RUNTIME VALIDATION REQUIRED

Centro Change viene costruito su Frappe Framework + ERPNext + Builder/Website + custom app `centrochange_core`.

## TD-002 — Upstream immutabile

**Stato:** PROPOSTA FORTE

Non modificare direttamente Frappe, ERPNext o Builder. Usare meccanismi di estensione supportati.

## TD-003 — Native-first

**Stato:** PROPOSTA FORTE

Ordine di scelta:

1. native;
2. extension;
3. official app;
4. custom `centrochange_core`;
5. external integration.

Criterio: qualità, sicurezza, tempo di sviluppo, manutenibilità/upgrade.

## TD-004 — Runtime locale

**Stato:** RUNTIME VALIDATION REQUIRED

Riutilizzare il workstation Windows/WSL2/Docker già disponibile come host, creando `centrochange-dev` come stack isolato. Riutilizzare pattern/tooling, non stato applicativo di altri progetti.

## TD-005 — Marley Health

**Stato:** OPEN / SPIKE REQUIRED

Prima di definire Patient/Practitioner/Appointment/Availability custom, valutare Marley Health sul runtime.

Esiti ammessi:

- riuso esteso;
- riuso selettivo;
- nessun riuso.

## TD-006 — Professionista

**Stato:** PROPOSTA

`Sales Person` non è identità operativa né security principal. Può essere proiezione economica opzionale.

## TD-007 — Pagamento MVP

**Stato:** PROPOSTA

Pagato Sì/No + metodo informativo non deve generare automaticamente `Payment Entry`. Usare settlement operativo separato, con pathway futuro verso Sales Invoice/Payment Entry.

## TD-008 — Pacchetti

**Stato:** PROPOSTA / SPIKE REQUIRED

Pacchetti custom con ledger append-oriented. Non forzare Product Bundle/Subscription se la semantica non coincide.

## TD-009 — Note

**Stato:** PROPOSTA FORTE / SECURITY CRITICAL

Separare `CC Organizational Note` e `CC Professional Note`, con permessi server-side e test anti-leakage.

## TD-010 — Git/Codex

**Stato:** OPERATIVO

- ChatGPT: architect/reviewer;
- Codex: runtime engineer/implementer;
- GitHub: source of truth tecnico;
- issue → branch → PR → evidence → review → merge.

## TD-011 — CC-CAP-020 Patient History / clinical feed

**Stato:** CONFERMATA DALL'OWNER — 2026-09-05

Classificazione capability: **EXTENSION**.

Decisione:

- riutilizzare la Patient History di Marley come base funzionale/UI;
- non usare i due endpoint PMR `get_feed` e `get_feed_for_dt` as-is nel perimetro professionisti assegnati;
- applicare in `centrochange_core` un'estensione supportata tramite override dei metodi whitelisted, con autorizzazione esplicita sul Patient e regression test own/cross-patient;
- non patchare Frappe o Marley core;
- mantenere come fallback un feed custom o l'esclusione della Patient History se l'override non mantiene il contratto/upgrade path richiesto.

Evidenza principale: Spike 02 `S02-PAT-013`–`S02-PAT-021`. I due endpoint PMR hanno FAIL runtime indipendenti sul confine di assegnazione; il guard esplicito sul Patient ha PASS semantico; il runtime Frappe espone `override_whitelisted_methods` come superficie di estensione supportata.

Questa decisione è limitata a **CC-CAP-020**. Non determina da sola l'esito complessivo Marley A/B/C e non approva automaticamente Patient Progress o altre capability Marley.

## Regola di aggiornamento

Quando uno spike produce evidenza sufficiente:

1. riportare evidenza nella issue/PR;
2. aggiornare la decisione da `RUNTIME VALIDATION REQUIRED` a stato confermato o sostituito;
3. documentare conseguenze e migrazioni;
4. non usare la parola `APPROVATO` come sostituto della decisione dell'utente/owner.