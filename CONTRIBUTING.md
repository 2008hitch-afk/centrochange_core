# Contributing — Centro Change

## Workflow

1. aprire o selezionare una issue;
2. verificare dipendenze e acceptance criteria;
3. creare branch `issue-<n>/<slug>`;
4. implementare il minimo necessario;
5. eseguire test;
6. aprire PR;
7. allegare evidenze runtime quando richieste;
8. review architetturale/requisiti prima del merge.

## Pull request

Ogni PR deve indicare:

- issue collegata;
- obiettivo;
- scope incluso/escluso;
- decisioni tecniche prese;
- test eseguiti;
- evidenze runtime;
- rischi residui;
- eventuali `RUNTIME VALIDATION REQUIRED` ancora aperti.

## Definition of Done minima

Una modifica è pronta per review solo se:

- non modifica core upstream;
- non contiene secret o dati reali;
- ha test proporzionati al rischio;
- le permission sono testate server-side quando pertinenti;
- le migrazioni sono ripetibili;
- eventuali job/queue sono idempotenti;
- documentazione/decisioni sono aggiornate quando cambia l'architettura.

## Convenzioni stato

Usare:

- `PROVEN NATIVE`
- `CONFIGURATION`
- `EXTENSION`
- `CUSTOM`
- `RUNTIME VALIDATION REQUIRED`

Per gli spike usare esito:

- `PASS`
- `PARTIAL`
- `FAIL`

`PASS` significa che gli acceptance criteria dichiarati sono stati verificati, non che l'intero sistema sia pronto per produzione.