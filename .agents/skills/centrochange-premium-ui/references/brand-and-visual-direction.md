# Brand e direzione grafica — Centro Change Premium

**Autorità:** HC-0005 DECISION-060 (direzione approvata); DECISION-061 (implementazione isolata autorizzata). Prima di tradurre la direzione in codice, verificare gli asset reali.

## Fonti

- Logo, colori e identità originale: https://www.centrochange.it/
- UX ispiratrice (non risorsa da copiare): https://www.fresha.com/
- UI library candidata: https://www.untitledui.com/react
- Calendar candidato: https://fullcalendar.io/ — verificare licenze Standard e Scheduler prima d'uso.
- Vecchia spec: `docs/ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md` è storica e superata per l'interfaccia React dove confligge con DECISION-060; non importare Tabler come obbligo.

## Audit brand

1. Identificare logo, header, favicon, SVG/raster e varianti con URL, proprietà, formato, dimensioni, trasparenza, stato di verifica e diritti; chiedere conferma se asset ufficiale ambiguo o non riutilizzabile.
2. Estrarre colori effettivi dalle CSS e dalla grafica originale, registrando valori e selettori/fonte; il vecchio `#12665F` è solo riferimento UI storico, non prova del colore istituzionale.
3. Ricostruire tokens semantici (primary, secondary, neutral, focus, success/warning/error, superfici, borders) con contrasto e theme supportati.
4. Verificare tipografia originale e licenze; non redistribuire font proprietari.
5. Versionare solo asset leciti; evitare CDN runtime non approvati.

## Esperienza Fresha-inspired, implementazione originale

- Agenda centrale, calendario leggibile per professionista e giorno/settimana, appuntamenti riconoscibili; niente griglia con geometria illeggibile.
- Shell unica: sidebar per ruolo, topbar essenziale, nessun Desk tecnico ERPNext/Frappe nel client-facing.
- Prenotazioni rapide, combobox unico e ricercabile per pazienti/professionisti, dettagli e azioni contestuali.
- Schede pazienti utili con storico, note e pacchetti, mai dati clinici riservati esposti oltre permessi.
- Finanza: task guidato, conti leggibili, importi/stati e documenti tracciabili, non solo elenco tecnico ERPNext.
- Mobile vero: touch, navigazione reflow, no overflow; keyboard e focus per desktop.
- Niente gradienti, badge, ombre o card decorative senza funzione; «premium» = qualità visiva + efficienza.

## Output richiesto

`BRAND-ASSET-AUDIT.md`, `DESIGN-TOKENS.json`, component catalog, reference e screenshot di Agenda/Pazienti/Finanza desktop/mobile, visual mismatch log e Owner visual validation separata da technical PASS.
